"""Social Token Manager — Store and manage social media access tokens.

Stores OAuth tokens per workspace per platform.
Supports: Facebook, Instagram, LinkedIn, Twitter/X, TikTok, YouTube

Token types:
- User Token (Explorer): 60 days, can manage pages + IG
- Page Token (long-lived): 60 days, can manage specific page
- IG Business Token: 60 days, can post to Instagram

Flow:
  1. Client gives email + password OR Explorer token
  2. Token saved in workspace
  3. Social Agent uses token to post via platform APIs
  4. Auto-renew reminder at 50th day
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Token storage directory
_TOKENS_DIR = Path(os.getenv("TAGS_TOKENS_DIR", "data/social_tokens"))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _workspace_dir(workspace_id: str) -> Path:
    """Get or create workspace token directory."""
    d = _TOKENS_DIR / workspace_id
    d.mkdir(parents=True, exist_ok=True)
    return d


# ═══════════════════════════════════════════════════════════════
# TOKEN STORAGE
# ═══════════════════════════════════════════════════════════════════════════════

def save_token(
    workspace_id: str,
    platform: str,
    access_token: str,
    platform_user_id: str = "",
    platform_username: str = "",
    page_id: str = "",
    page_name: str = "",
    ig_account_id: str = "",
    ig_username: str = "",
    expires_at: str = "",
    token_type: str = "user_token",
    scopes: list[str] | None = None,
) -> dict[str, Any]:
    """Save a social media access token for a workspace.

    Args:
        workspace_id: Workspace ID
        platform: facebook, instagram, linkedin, twitter, tiktok, youtube
        access_token: The OAuth access token
        platform_user_id: Platform user ID
        platform_username: Platform username
        page_id: Facebook Page ID (if applicable)
        page_name: Facebook Page name
        ig_account_id: Instagram Business Account ID
        ig_username: Instagram username
        expires_at: Token expiry datetime (ISO format)
        token_type: user_token, page_token, long_lived_token
        scopes: List of permissions/scopes granted
    """
    d = _workspace_dir(workspace_id)

    token_data = {
        "platform": platform,
        "access_token": access_token,
        "platform_user_id": platform_user_id,
        "platform_username": platform_username,
        "page_id": page_id,
        "page_name": page_name,
        "ig_account_id": ig_account_id,
        "ig_username": ig_username,
        "expires_at": expires_at,
        "token_type": token_type,
        "scopes": scopes or [],
        "connected_at": _now(),
        "last_used_at": "",
        "status": "active",
    }

    # Save per-platform file
    token_file = d / f"{platform}.json"
    token_file.write_text(json.dumps(token_data, indent=2), encoding="utf-8")

    logger.info("Token saved: %s/%s (type=%s, expires=%s)", workspace_id, platform, token_type, expires_at)
    return {"status": "saved", "platform": platform, "token_type": token_type, "expires_at": expires_at}


def get_token(workspace_id: str, platform: str) -> dict[str, Any] | None:
    """Get stored token for a platform. Returns None if not found or expired."""
    d = _workspace_dir(workspace_id)
    token_file = d / f"{platform}.json"

    if not token_file.exists():
        return None

    try:
        data = json.loads(token_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None

    # Check expiry
    expires_at = data.get("expires_at", "")
    if expires_at:
        try:
            exp = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            if datetime.now(timezone.utc) > exp:
                data["status"] = "expired"
                return data
        except ValueError:
            pass

    # Update last used
    data["last_used_at"] = _now()
    token_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    return data


def list_tokens(workspace_id: str) -> list[dict[str, Any]]:
    """List all connected accounts for a workspace."""
    d = _workspace_dir(workspace_id)
    tokens = []

    for f in sorted(d.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            # Check expiry
            expires_at = data.get("expires_at", "")
            if expires_at:
                try:
                    exp = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                    if datetime.now(timezone.utc) > exp:
                        data["status"] = "expired"
                except ValueError:
                    pass

            # Don't expose full token in list
            safe = {k: v for k, v in data.items() if k != "access_token"}
            safe["has_token"] = bool(data.get("access_token"))
            tokens.append(safe)
        except (json.JSONDecodeError, OSError):
            continue

    return tokens


def delete_token(workspace_id: str, platform: str) -> dict[str, Any]:
    """Delete a stored token."""
    d = _workspace_dir(workspace_id)
    token_file = d / f"{platform}.json"

    if token_file.exists():
        token_file.unlink()
        return {"status": "deleted", "platform": platform}
    return {"status": "not_found", "platform": platform}


def get_active_token(workspace_id: str, platform: str) -> str | None:
    """Get just the access token string (for API calls). Returns None if not found/expired."""
    data = get_token(workspace_id, platform)
    if data and data.get("status") == "active":
        return data.get("access_token")
    return None


def get_token_expiry_info(workspace_id: str, platform: str) -> dict[str, Any]:
    """Check token status — active, expiring soon, or expired."""
    data = get_token(workspace_id, platform)
    if not data:
        return {"status": "not_connected", "platform": platform}

    expires_at = data.get("expires_at", "")
    if not expires_at:
        return {"status": "active", "platform": platform, "expires_at": "unknown"}

    try:
        exp = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        days_left = (exp - now).days

        if days_left < 0:
            status = "expired"
        elif days_left <= 10:
            status = "expiring_soon"
        else:
            status = "active"

        return {
            "status": status,
            "platform": platform,
            "expires_at": expires_at,
            "days_left": max(days_left, 0),
            "needs_renewal": days_left <= 10,
        }
    except ValueError:
        return {"status": "active", "platform": platform, "expires_at": expires_at}


# ═══════════════════════════════════════════════════════════════════════════════
# FACEBOOK / INSTAGRAM TOKEN EXCHANGE
# ═══════════════════════════════════════════════════════════════════════════════

def exchange_facebook_token(
    workspace_id: str,
    explorer_token: str,
    app_id: str = "",
    app_secret: str = "",
) -> dict[str, Any]:
    """Exchange a Facebook Explorer token for a long-lived token.

    Explorer token (from Graph API Explorer) is valid for ~1 hour.
    This exchanges it for a long-lived token valid for 60 days.

    Then fetches pages and IG business accounts.
    """
    import requests

    result = {
        "workspace_id": workspace_id,
        "exchange_status": "pending",
        "pages": [],
        "ig_accounts": [],
    }

    # Step 1: Exchange for long-lived token
    if app_id and app_secret:
        try:
            exchange_resp = requests.get(
                "https://graph.facebook.com/v19.0/oauth/access_token",
                params={
                    "grant_type": "fb_exchange_token",
                    "client_id": app_id,
                    "client_secret": app_secret,
                    "fb_exchange_token": explorer_token,
                },
                timeout=15,
            )
            if exchange_resp.ok:
                data = exchange_resp.json()
                long_lived_token = data.get("access_token", explorer_token)
                result["exchange_status"] = "exchanged"
                result["token_type"] = "long_lived_token"
            else:
                long_lived_token = explorer_token
                result["exchange_status"] = "exchange_failed_using_explorer"
                result["exchange_error"] = exchange_resp.text[:200]
        except Exception as e:
            long_lived_token = explorer_token
            result["exchange_status"] = "exchange_error_using_explorer"
            result["exchange_error"] = str(e)[:200]
    else:
        # No app credentials — use explorer token directly
        long_lived_token = explorer_token
        result["exchange_status"] = "using_explorer_directly"
        result["note"] = "No App ID/Secret provided. Using Explorer token directly. Add App ID/Secret for long-lived tokens."

    # Step 2: Get user info
    user_info = {}
    try:
        me_resp = requests.get(
            "https://graph.facebook.com/v19.0/me",
            params={"fields": "id,name,email", "access_token": long_lived_token},
            timeout=15,
        )
        if me_resp.ok:
            user_info = me_resp.json()
    except Exception:
        pass

    # Step 3: Get pages
    try:
        pages_resp = requests.get(
            "https://graph.facebook.com/v19.0/me/accounts",
            params={"access_token": long_lived_token},
            timeout=15,
        )
        if pages_resp.ok:
            pages_data = pages_resp.json().get("data", [])
            for page in pages_data:
                page_info = {
                    "id": page.get("id", ""),
                    "name": page.get("name", ""),
                    "access_token": page.get("access_token", ""),
                    "category": page.get("category", ""),
                }

                # Step 4: Get IG business account for this page
                try:
                    ig_resp = requests.get(
                        f"https://graph.facebook.com/v19.0/{page['id']}",
                        params={
                            "fields": "instagram_business_account{id,username,name}",
                            "access_token": page.get("access_token", long_lived_token),
                        },
                        timeout=15,
                    )
                    if ig_resp.ok:
                        ig_data = ig_resp.json().get("instagram_business_account", {})
                        if ig_data:
                            page_info["ig_account_id"] = ig_data.get("id", "")
                            page_info["ig_username"] = ig_data.get("username", "")
                            result["ig_accounts"].append({
                                "id": ig_data.get("id", ""),
                                "username": ig_data.get("username", ""),
                                "name": ig_data.get("name", ""),
                                "page_id": page.get("id", ""),
                                "page_name": page.get("name", ""),
                            })
                except Exception:
                    pass

                result["pages"].append(page_info)

    except Exception as e:
        result["pages_error"] = str(e)[:200]

    # Step 5: Save tokens
    expires = (datetime.now(timezone.utc) + timedelta(days=60)).isoformat()

    # Save main user token
    save_token(
        workspace_id=workspace_id,
        platform="facebook",
        access_token=long_lived_token,
        platform_user_id=user_info.get("id", ""),
        platform_username=user_info.get("name", ""),
        expires_at=expires,
        token_type=result.get("token_type", "explorer_token"),
        scopes=["pages_manage_posts", "pages_read_engagement", "instagram_basic", "instagram_content_publish"],
    )

    # Save page tokens and IG tokens
    for page in result["pages"]:
        page_token = page.get("access_token", long_lived_token)
        page_expires = (datetime.now(timezone.utc) + timedelta(days=60)).isoformat()

        save_token(
            workspace_id=workspace_id,
            platform=f"facebook_page_{page['id']}",
            access_token=page_token,
            page_id=page["id"],
            page_name=page["name"],
            expires_at=page_expires,
            token_type="page_token",
        )

        if page.get("ig_account_id"):
            save_token(
                workspace_id=workspace_id,
                platform="instagram",
                access_token=page_token,  # Page token works for IG too
                ig_account_id=page["ig_account_id"],
                ig_username=page.get("ig_username", ""),
                page_id=page["id"],
                page_name=page["name"],
                expires_at=page_expires,
                token_type="page_token",
            )

    result["user_info"] = user_info
    result["token_saved"] = True
    result["expires_at"] = expires

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# POST TO FACEBOOK
# ═══════════════════════════════════════════════════════════════════════════════

def post_to_facebook(
    workspace_id: str,
    page_id: str,
    message: str,
    image_url: str = "",
    link: str = "",
) -> dict[str, Any]:
    """Post to a Facebook Page using stored token."""
    import requests

    token = get_active_token(workspace_id, f"facebook_page_{page_id}")
    if not token:
        # Try main facebook token
        token = get_active_token(workspace_id, "facebook")
    if not token:
        return {"status": "error", "error": "No active Facebook token. Please reconnect."}

    post_data: dict[str, Any] = {"message": message}
    if image_url:
        post_data["link"] = image_url  # FB API uses 'link' for image posts
    if link:
        post_data["link"] = link

    try:
        resp = requests.post(
            f"https://graph.facebook.com/v19.0/{page_id}/feed",
            params={"access_token": token},
            data=post_data,
            timeout=30,
        )
        if resp.ok:
            result = resp.json()
            return {
                "status": "published",
                "platform": "facebook",
                "post_id": result.get("id", ""),
                "published_at": _now(),
            }
        else:
            return {
                "status": "error",
                "platform": "facebook",
                "error": resp.text[:500],
            }
    except Exception as e:
        return {"status": "error", "platform": "facebook", "error": str(e)[:300]}


# ═══════════════════════════════════════════════════════════════════════════════
# POST TO INSTAGRAM
# ═══════════════════════════════════════════════════════════════════════════════

def post_to_instagram(
    workspace_id: str,
    ig_account_id: str,
    image_url: str,
    caption: str,
) -> dict[str, Any]:
    """Post to Instagram Business account using stored token.

    IG media publish flow:
    1. Create media container (POST /media)
    2. Wait for container to be ready
    3. Publish container (POST /media_publish)
    """
    import requests
    import time

    token = get_active_token(workspace_id, "instagram")
    if not token:
        return {"status": "error", "error": "No active Instagram token. Please reconnect."}

    # Step 1: Create media container
    try:
        container_resp = requests.post(
            f"https://graph.facebook.com/v19.0/{ig_account_id}/media",
            params={"access_token": token},
            data={
                "image_url": image_url,
                "caption": caption,
            },
            timeout=30,
        )
        if not container_resp.ok:
            return {"status": "error", "platform": "instagram", "error": container_resp.text[:500]}

        container_id = container_resp.json().get("id", "")
        if not container_id:
            return {"status": "error", "platform": "instagram", "error": "No container ID returned"}
    except Exception as e:
        return {"status": "error", "platform": "instagram", "error": str(e)[:300]}

    # Step 2: Wait for container to be ready (max 60 seconds)
    for _ in range(12):
        time.sleep(5)
        try:
            status_resp = requests.get(
                f"https://graph.facebook.com/v19.0/{container_id}",
                params={"fields": "status_code", "access_token": token},
                timeout=15,
            )
            if status_resp.ok:
                status = status_resp.json().get("status_code", "")
                if status == "FINISHED":
                    break
                elif status == "ERROR":
                    return {"status": "error", "platform": "instagram", "error": "Media container processing failed"}
        except Exception:
            pass

    # Step 3: Publish
    try:
        publish_resp = requests.post(
            f"https://graph.facebook.com/v19.0/{ig_account_id}/media_publish",
            params={"access_token": token},
            data={"creation_id": container_id},
            timeout=30,
        )
        if publish_resp.ok:
            post_id = publish_resp.json().get("id", "")
            return {
                "status": "published",
                "platform": "instagram",
                "post_id": post_id,
                "published_at": _now(),
            }
        else:
            return {"status": "error", "platform": "instagram", "error": publish_resp.text[:500]}
    except Exception as e:
        return {"status": "error", "platform": "instagram", "error": str(e)[:300]}
