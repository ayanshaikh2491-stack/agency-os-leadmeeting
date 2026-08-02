"""
Facebook/Instagram OAuth 2.0 Handler — Graph API v18.0

Handles the complete OAuth flow:
1. Generate OAuth authorize URL
2. Exchange authorization code for short-lived token
3. Exchange short-lived token for long-lived token (60 days)
4. Extract Page Access Token
5. Get Instagram Business Account ID (if linked)
6. Save tokens to Supabase social_accounts table

Config (env vars):
  FACEBOOK_APP_ID
  FACEBOOK_APP_SECRET
  FRONTEND_URL
  SUPABASE_URL
  SUPABASE_SERVICE_ROLE_KEY
"""

import os
import json
import httpx
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from urllib.parse import urlencode

# ── Configuration ──────────────────────────────────────────────────────────────

FACEBOOK_APP_ID = os.environ.get("FACEBOOK_APP_ID", "")
FACEBOOK_APP_SECRET = os.environ.get("FACEBOOK_APP_SECRET", "")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")
SUPABASE_URL = os.environ.get("SUPABASE_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY", "")

# Graph API v20.0 (2026 stable)
GRAPH_API_VERSION = "v20.0"
FACEBOOK_OAUTH_URL = f"https://www.facebook.com/{GRAPH_API_VERSION}/dialog/oauth"
FACEBOOK_TOKEN_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}/oauth/access_token"

# OAuth scopes for Facebook Page + Instagram Business (2026 updated)
# business_management is REQUIRED for pages linked to Meta Business Portfolio
FACEBOOK_SCOPES = [
    "pages_manage_posts",
    "pages_read_engagement",
    "pages_show_list",
    "pages_manage_metadata",
    "pages_read_user_content",
    "pages_manage_engagement",
    "business_management",
    "public_profile",
    "instagram_basic",
    "instagram_content_publish",
    "instagram_manage_comments",
    "instagram_manage_insights",
]


# ── OAuth Flow ─────────────────────────────────────────────────────────────────


def get_facebook_auth_url(client_name: str, platform: str = "facebook", redirect_to: str = "") -> str:
    """Generate the Facebook OAuth 2.0 authorize URL.

    Args:
        client_name: Unique identifier for the client connecting their account.
        platform: 'facebook' or 'instagram' — determines callback URL.
        redirect_to: Where to redirect after OAuth (e.g. /dashboard/social or /client/social).

    Returns:
        Full OAuth authorize URL. Redirects back to the correct callback.
    """
    if not FACEBOOK_APP_ID:
        raise ValueError("FACEBOOK_APP_ID not configured")

    # State encodes client_name, platform, and redirect path
    # Format: client_name:platform:redirect_path
    # Use URL-safe encoding for the redirect path
    import base64
    if redirect_to:
        encoded_redirect = base64.urlsafe_b64encode(redirect_to.encode()).decode()
        state = f"{client_name}:{platform}:{encoded_redirect}"
    else:
        state = f"{client_name}:{platform}"

    params = {
        "client_id": FACEBOOK_APP_ID,
        "redirect_uri": f"{FRONTEND_URL}/api/social/oauth/{platform}/callback",
        "scope": ",".join(FACEBOOK_SCOPES),
        "response_type": "code",
        "state": state,
        "auth_type": "reauthenticate",  # Force Facebook to always show login page
    }
    return f"{FACEBOOK_OAUTH_URL}?{urlencode(params)}"


def _parse_state(state: str) -> tuple:
    """Parse OAuth state parameter.

    State format: client_name[:platform[:base64_redirect_path]]

    Returns:
        Tuple of (client_name, platform, redirect_path)
        redirect_path defaults to /client/social if not found.
    """
    if not state:
        return ("default", "facebook", "/client/social")

    parts = state.split(":")
    client_name = parts[0]
    platform = parts[1] if len(parts) > 1 else "facebook"
    redirect_path = "/client/social"

    if len(parts) > 2:
        # The redirect path is base64-encoded (it may contain `/` which would split on `:`)
        import base64
        try:
            encoded = parts[2]
            # Handle case where state has more parts (encoded data could have no padding)
            redirect_path = base64.urlsafe_b64decode(encoded).decode()
        except Exception:
            # Fallback
            redirect_path = "/client/social"

    return (client_name, platform, redirect_path)


async def handle_facebook_callback(
    code: str, state: str, client_name: Optional[str] = None
) -> Dict[str, Any]:
    """Handle Facebook OAuth callback: exchange code → tokens → save to Supabase.

    Full flow:
    1. Exchange authorization code for short-lived user token
    2. Exchange short-lived token for long-lived token (60 days)
    3. Get Page Access Token from user token
    4. Get Instagram Business Account ID (if linked to Page)
    5. Save everything to Supabase

    Args:
        code: Authorization code from Facebook callback.
        state: State parameter (client_name:platform[:base64_redirect]).
        client_name: Override for client name (uses state if not provided).

    Returns:
        Dict with success status, redirect URL, and token metadata.
    """
    # Parse full state to get name, platform, and redirect path
    state_name, _, redirect_path = _parse_state(state)
    name = client_name or state_name
    if not name:
        redirect_path = "/client/social"
        return {"success": False, "error": "Missing client_name", "redirect": f"{FRONTEND_URL}{redirect_path}?error=no_client"}

    def _build_redirect(error_key="", extra_params=None):
        """Build redirect URL to the right page (dashboard or client)."""
        base = f"{FRONTEND_URL}{redirect_path}"
        if error_key:
            params = f"?{error_key}"
            if extra_params:
                params += f"&{extra_params}"
            return base + params
        return base

    try:
        # Step 1: Exchange code for short-lived token
        short_token_data = await _exchange_code_for_token(code)
        if not short_token_data.get("success"):
            return {
                "success": False,
                "error": short_token_data.get("error", "Failed to get token"),
                "redirect": _build_redirect("error=token_exchange_failed&platform=facebook"),
            }

        short_token = short_token_data["access_token"]

        # Step 2: Exchange for long-lived token (60 days)
        long_token_data = await get_long_lived_token(short_token)
        if not long_token_data.get("success"):
            # Fallback: use short-lived token if exchange fails
            long_token_data = {"success": True, "access_token": short_token, "expires_in": 3600}

        long_token = long_token_data["access_token"]
        expires_in = long_token_data.get("expires_in", 5184000)  # 60 days default
        expires_at = (datetime.now(timezone.utc) + timedelta(seconds=expires_in)).isoformat()

        # Step 3: Get Page Access Token
        page_data = await _get_page_access_token(long_token)
        if not page_data.get("success"):
            return {
                "success": False,
                "error": page_data.get("error", "Failed to get page token"),
                "redirect": _build_redirect("error=page_token_failed&platform=facebook"),
            }

        page_token = page_data["access_token"]
        page_id = page_data.get("page_id", "")
        page_name = page_data.get("page_name", "")

        # Step 4: Get Instagram Business Account ID (if linked)
        ig_business_id = None
        ig_username = None
        ig_data = await get_instagram_business_id(page_token, page_id)
        if ig_data.get("success") and ig_data.get("instagram_business_id"):
            ig_business_id = ig_data.get("instagram_business_id")
            # Fetch IG username
            username_data = await get_instagram_username(page_token, ig_business_id)
            if username_data.get("success"):
                ig_username = username_data.get("username")

        # Step 5: Save Facebook to Supabase
        token_data = {
            "access_token": page_token,
            "user_token": long_token,
            "token_expires_at": expires_at,
            "account_id": page_id,
            "meta": {
                "page_id": page_id,
                "page_name": page_name,
                "instagram_id": ig_business_id,
                "scopes": FACEBOOK_SCOPES,
            },
        }

        save_result = await save_token_to_supabase(name, "facebook", token_data)
        if not save_result.get("success"):
            return {
                "success": False,
                "error": save_result.get("error", "Failed to save token"),
                "redirect": _build_redirect("error=save_failed&platform=facebook"),
            }

        # Step 6: If IG is linked, save IG record too
        if ig_business_id:
            ig_token_data = {
                "access_token": page_token,  # IG uses Page token for posting
                "user_token": long_token,
                "token_expires_at": expires_at,
                "account_id": ig_business_id,
                "meta": {
                    "ig_username": ig_username,
                    "fb_page_id": page_id,
                    "fb_page_name": page_name,
                    "scopes": FACEBOOK_SCOPES,
                },
            }
            await save_token_to_supabase(name, "instagram", ig_token_data)

        return {
            "success": True,
            "redirect": _build_redirect("success=facebook_connected", f"page_name={page_name}"),
            "page_id": page_id,
            "page_name": page_name,
            "instagram_connected": ig_business_id is not None,
            "token_expires_at": expires_at,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "redirect": _build_redirect("error=callback_error&platform=facebook"),
        }


async def find_all_instagram_accounts(user_token: str) -> Dict[str, Any]:
    """Search all managed pages for linked Instagram Business Accounts."""
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/me/accounts"
    params = {"access_token": user_token}
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, params=params)
            data = resp.json()
        if "error" in data:
            return {"success": False, "error": data["error"].get("message")}
        pages = data.get("data", [])
        ig_accounts = []
        for page in pages:
            page_id = page.get("id")
            page_name = page.get("name")
            page_token = page.get("access_token")
            ig_url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{page_id}"
            ig_params = {"fields": "instagram_business_account", "access_token": page_token}
            async with httpx.AsyncClient(timeout=15) as client:
                ig_resp = await client.get(ig_url, params=ig_params)
                ig_data = ig_resp.json()
            ig_account = ig_data.get("instagram_business_account")
            if ig_account and ig_account.get("id"):
                ig_id = ig_account["id"]
                uname_url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{ig_id}"
                uname_params = {"fields": "username", "access_token": page_token}
                async with httpx.AsyncClient(timeout=15) as client:
                    uname_resp = await client.get(uname_url, params=uname_params)
                    uname_data = uname_resp.json()
                ig_accounts.append({
                    "ig_id": ig_id,
                    "ig_username": uname_data.get("username"),
                    "page_id": page_id,
                    "page_name": page_name,
                    "page_token": page_token,
                })
        if not ig_accounts:
            return {"success": False, "error": "No Instagram Business Account found. Please link Instagram to a Facebook Page first."}
        return {"success": True, "accounts": ig_accounts}
    except httpx.RequestError as e:
        return {"success": False, "error": f"Request failed: {str(e)}"}


async def save_instagram_account(client_name: str, ig_account: Dict[str, Any], long_token: str, expires_at: str) -> Dict[str, Any]:
    """Save a selected Instagram account to Supabase."""
    token_data = {
        "access_token": ig_account["page_token"],
        "user_token": long_token,
        "token_expires_at": expires_at,
        "account_id": ig_account["ig_id"],
        "meta": {
            "ig_username": ig_account["ig_username"],
            "fb_page_id": ig_account["page_id"],
            "fb_page_name": ig_account["page_name"],
            "scopes": FACEBOOK_SCOPES,
        },
    }
    return await save_token_to_supabase(client_name, "instagram", token_data)


async def handle_instagram_callback(
    code: str, state: str, client_name: Optional[str] = None
) -> Dict[str, Any]:
    """Handle Instagram OAuth callback: search all pages for IG and return list for selection."""
    state_name, _, redirect_path = _parse_state(state)
    name = client_name or state_name
    if not name:
        return {"success": False, "error": "Missing client_name", "redirect": f"{FRONTEND_URL}{redirect_path}?error=no_client"}
    try:
        short_token_data = await _exchange_code_for_token(code, platform="instagram")
        if not short_token_data.get("success"):
            return {"success": False, "error": short_token_data.get("error"), "redirect": f"{FRONTEND_URL}{redirect_path}?error=token_failed&platform=instagram"}
        short_token = short_token_data["access_token"]
        long_token_data = await get_long_lived_token(short_token)
        if not long_token_data.get("success"):
            long_token_data = {"success": True, "access_token": short_token, "expires_in": 3600}
        long_token = long_token_data["access_token"]
        expires_in = long_token_data.get("expires_in", 5184000)
        expires_at = (datetime.now(timezone.utc) + timedelta(seconds=expires_in)).isoformat()

        # Store long token and expiry temporarily for selection step
        # We'll pass them via state or store in session (for now, use redirect params)
        ig_result = await find_all_instagram_accounts(long_token)
        if not ig_result.get("success"):
            error_msg = ig_result.get("error", "No Instagram Business Account found")
            # URL-encode the detailed error message so frontend can show it
            import urllib.parse
            detailed_error = urllib.parse.quote(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "redirect": f"{FRONTEND_URL}{redirect_path}?error=instagram_not_found&platform=instagram&detail={detailed_error}"
            }

        accounts = ig_result["accounts"]
        # Include the redirect_path so frontend can use it for the final redirect
        return {
            "success": True,
            "needs_selection": True,
            "accounts": accounts,
            "long_token": long_token,
            "expires_at": expires_at,
            "client_name": name,
            "redirect_path": redirect_path,
        }
    except Exception as e:
        return {"success": False, "error": str(e), "redirect": f"{FRONTEND_URL}{redirect_path}?error=callback_error&platform=instagram"}


# ── Token Exchange ─────────────────────────────────────────────────────────────


async def _exchange_code_for_token(code: str, platform: str = "facebook") -> Dict[str, Any]:
    """Exchange OAuth authorization code for a short-lived access token.

    Args:
        code: Authorization code from Facebook callback.
        platform: 'facebook' or 'instagram' - determines the redirect_uri match.

    Returns:
        Dict with access_token, token_type, and expires_in (~1 hour).
    """
    if not FACEBOOK_APP_ID or not FACEBOOK_APP_SECRET:
        return {"success": False, "error": "Facebook app credentials not configured"}

    # Redirect URI MUST exactly match the one used in the authorize URL
    # Facebook validates this - mismatch causes token exchange failure
    redirect_uri = f"{FRONTEND_URL}/api/social/oauth/{platform}/callback"

    params = {
        "client_id": FACEBOOK_APP_ID,
        "client_secret": FACEBOOK_APP_SECRET,
        "redirect_uri": redirect_uri,
        "code": code,
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(FACEBOOK_TOKEN_URL, params=params)
            data = resp.json()

        if "error" in data:
            return {"success": False, "error": data["error"].get("message", str(data["error"]))}

        return {
            "success": True,
            "access_token": data["access_token"],
            "token_type": data.get("token_type", "bearer"),
            "expires_in": data.get("expires_in", 3600),
        }
    except httpx.RequestError as e:
        return {"success": False, "error": f"Request failed: {str(e)}"}
    except (json.JSONDecodeError, KeyError) as e:
        return {"success": False, "error": f"Invalid response: {str(e)}"}


async def get_long_lived_token(short_token: str) -> Dict[str, Any]:
    """Exchange a short-lived token (~1 hour) for a long-lived token (~60 days).

    Uses the Graph API token exchange endpoint.

    Args:
        short_token: Short-lived user access token.

    Returns:
        Dict with long-lived access_token and expires_in (~5,184,000 seconds = 60 days).
    """
    if not FACEBOOK_APP_ID or not FACEBOOK_APP_SECRET:
        return {"success": False, "error": "Facebook app credentials not configured"}

    params = {
        "grant_type": "fb_exchange_token",
        "client_id": FACEBOOK_APP_ID,
        "client_secret": FACEBOOK_APP_SECRET,
        "fb_exchange_token": short_token,
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(FACEBOOK_TOKEN_URL, params=params)
            data = resp.json()

        if "error" in data:
            return {"success": False, "error": data["error"].get("message", str(data["error"]))}

        return {
            "success": True,
            "access_token": data["access_token"],
            "token_type": data.get("token_type", "bearer"),
            "expires_in": data.get("expires_in", 5184000),
        }
    except httpx.RequestError as e:
        return {"success": False, "error": f"Request failed: {str(e)}"}
    except (json.JSONDecodeError, KeyError) as e:
        return {"success": False, "error": f"Invalid response: {str(e)}"}


# ── Page & Instagram ───────────────────────────────────────────────────────────


async def _get_page_access_token(user_token: str) -> Dict[str, Any]:
    """Get the first available Page Access Token from a user token.

    Fetches the user's pages and returns the access token for the first page.
    The page token inherits the expiry of the user token.

    Args:
        user_token: Long-lived user access token.

    Returns:
        Dict with page access_token, page_id, and page_name.
    """
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/me/accounts"
    params = {"access_token": user_token}

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, params=params)
            data = resp.json()

        if "error" in data:
            return {"success": False, "error": data["error"].get("message", str(data["error"]))}

        pages = data.get("data", [])
        if not pages:
            return {"success": False, "error": "No Facebook Pages found. Connect a Page first."}

        # Return the first page (can be extended to let user choose)
        page = pages[0]
        return {
            "success": True,
            "access_token": page["access_token"],
            "page_id": page["id"],
            "page_name": page["name"],
        }
    except httpx.RequestError as e:
        return {"success": False, "error": f"Request failed: {str(e)}"}
    except (json.JSONDecodeError, KeyError) as e:
        return {"success": False, "error": f"Invalid response: {str(e)}"}


async def get_instagram_business_id(page_token: str, page_id: str) -> Dict[str, Any]:
    """Get the Instagram Business Account ID linked to a Facebook Page.

    Queries the Page's ig_business_account field.

    Args:
        page_token: Page access token.
        page_id: Facebook Page ID.

    Returns:
        Dict with instagram_business_id if linked, or success=True with None if not linked.
    """
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{page_id}"
    params = {
        "fields": "instagram_business_account",
        "access_token": page_token,
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, params=params)
            data = resp.json()

        if "error" in data:
            # Not an error — page just might not have IG linked
            return {"success": True, "instagram_business_id": None, "note": "No Instagram Business Account linked"}

        ig_account = data.get("instagram_business_account")
        if ig_account:
            return {
                "success": True,
                "instagram_business_id": ig_account.get("id"),
                "ig_username": ig_account.get("username"),
            }

        return {"success": True, "instagram_business_id": None, "note": "No Instagram Business Account linked"}
    except httpx.RequestError as e:
        return {"success": True, "instagram_business_id": None, "note": f"Request failed: {str(e)}"}
    except (json.JSONDecodeError, KeyError) as e:
        return {"success": True, "instagram_business_id": None, "note": f"Parse error: {str(e)}"}


async def get_instagram_username(page_token: str, ig_id: str) -> Dict[str, Any]:
    """Get the Instagram username for a Business Account.

    Args:
        page_token: Page access token.
        ig_id: Instagram Business Account ID.

    Returns:
        Dict with username.
    """
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{ig_id}"
    params = {
        "fields": "username",
        "access_token": page_token,
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, params=params)
            data = resp.json()

        if "error" in data:
            return {"success": False, "error": data["error"].get("message")}

        return {
            "success": True,
            "username": data.get("username"),
        }
    except httpx.RequestError as e:
        return {"success": False, "error": str(e)}


# ── Aliases for main.py compatibility ──────────────────────────────────────────

# main.py imports these names — alias to the facebook-specific functions
get_authorize_url = get_facebook_auth_url

async def handle_callback(platform: str, code: str, state: str) -> str:
    """Router for main.py OAuth callback endpoint.

    Dispatches to the correct platform handler based on platform string.

    Args:
        platform: "facebook" or "instagram".
        code: OAuth authorization code.
        state: State parameter (client_name).

    Returns:
        Redirect URL string.
    """
    if platform == "instagram":
        result = await handle_instagram_callback(code, state)
    else:
        result = await handle_facebook_callback(code, state)
    return result.get("redirect", f"{FRONTEND_URL}/client/social?error=unknown_platform")


# ── Supabase Integration ───────────────────────────────────────────────────────


async def save_token_to_supabase(
    client_name: str, platform: str, token_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Save OAuth token data to Supabase social_accounts table.

    Uses UPSERT (on_conflict on client_name + platform) so reconnecting
    an account updates the existing record instead of creating duplicates.

    Table columns:
        client_name, platform, access_token, refresh_token,
        token_expires_at, account_id, meta (JSONB), status

    Args:
        client_name: Unique client identifier.
        platform: "facebook" or "instagram".
        token_data: Dict with access_token, token_expires_at, account_id, meta.

    Returns:
        Dict with success status.
    """
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return {"success": False, "error": "Supabase not configured"}

    payload = {
        "client_name": client_name,
        "platform": platform,
        "access_token": token_data.get("access_token", ""),
        "refresh_token": token_data.get("user_token", ""),
        "token_expires_at": token_data.get("token_expires_at"),
        "account_id": token_data.get("account_id"),
        "meta": token_data.get("meta", {}),
        "status": "connected",
    }

    try:
        url = f"{SUPABASE_URL}/rest/v1/social_accounts?on_conflict=client_name,platform"
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                url,
                headers={
                    "apikey": SUPABASE_SERVICE_KEY,
                    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                    "Content-Type": "application/json",
                    "Prefer": "resolution=merge-duplicates",
                },
                json=payload,
            )

        if resp.status_code in (200, 201, 204):
            return {"success": True}

        error_body = resp.text[:200]
        return {"success": False, "error": f"Supabase error {resp.status_code}: {error_body}"}
    except httpx.RequestError as e:
        return {"success": False, "error": f"Request failed: {str(e)}"}


async def get_account_status(client_name: str) -> Dict[str, Any]:
    """Get connected social account status for a client.

    Queries Supabase for all platforms connected to the given client_name.

    Args:
        client_name: Unique client identifier.

    Returns:
        Dict with platform → {status, account_id, token_expires_at, meta} mapping.
    """
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return {"error": "Supabase not configured", "accounts": {}}

    try:
        from urllib.parse import quote
        encoded_name = quote(client_name)
        url = f"{SUPABASE_URL}/rest/v1/social_accounts?client_name=eq.{encoded_name}&select=platform,status,account_id,token_expires_at,meta"

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                url,
                headers={
                    "apikey": SUPABASE_SERVICE_KEY,
                    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                },
            )

        if resp.status_code != 200:
            return {"error": f"Supabase error {resp.status_code}", "accounts": {}}

        accounts = resp.json()
        result = {}
        for acct in accounts:
            platform = acct["platform"]
            result[platform] = {
                "status": acct.get("status", "unknown"),
                "account_id": acct.get("account_id"),
                "token_expires_at": acct.get("token_expires_at"),
                "meta": acct.get("meta", {}),
            }

        return {"accounts": result, "connected_count": len(result)}
    except httpx.RequestError as e:
        return {"error": str(e), "accounts": {}}


async def disconnect_account(client_name: str, platform: str) -> Dict[str, Any]:
    """Remove a connected social account from Supabase.

    Deletes the row matching client_name + platform from social_accounts table.

    Args:
        client_name: Unique client identifier.
        platform: "facebook" or "instagram" or other platform name.

    Returns:
        Dict with success status.
    """
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return {"success": False, "error": "Supabase not configured"}

    try:
        from urllib.parse import quote
        encoded_name = quote(client_name)
        encoded_platform = quote(platform)
        url = f"{SUPABASE_URL}/rest/v1/social_accounts?client_name=eq.{encoded_name}&platform=eq.{encoded_platform}"

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.delete(
                url,
                headers={
                    "apikey": SUPABASE_SERVICE_KEY,
                    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                },
            )

        if resp.status_code in (200, 204):
            return {"success": True, "platform": platform, "client_name": client_name}

        return {"success": False, "error": f"Supabase error {resp.status_code}"}
    except httpx.RequestError as e:
        return {"success": False, "error": str(e)}
