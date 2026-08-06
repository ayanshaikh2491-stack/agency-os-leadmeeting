# admin/tools/organic/reddit_api.py
"""Reddit posting via OAuth2 script app (raw requests, no PRAW dependency)."""
from __future__ import annotations

import logging

import requests

from admin.tools.organic.base import CHANNEL_TYPE_API, PostResult
from admin.tools.organic.config import get_channel_config
from admin.token_manager import get_active_token

logger = logging.getLogger(__name__)

CHANNEL_META = {
    "id": "reddit",
    "name": "Reddit",
    "type": CHANNEL_TYPE_API,
    "auth": "token",
    "capabilities": ["post", "comment"],
    "required_fields": ["subreddit", "title", "body"],
    "description": "Post to subreddits and comment on threads.",
}

REDDIT_OAUTH_URL = "https://www.reddit.com/api/v1/access_token"
REDDIT_API_URL = "https://oauth.reddit.com"


def _get_access_token(client_id: str, client_secret: str, username: str, password: str) -> str | None:
    try:
        resp = requests.post(
            REDDIT_OAUTH_URL,
            auth=(client_id, client_secret),
            data={"grant_type": "password", "username": username, "password": password},
            headers={"User-Agent": "AgencyOrganicBot/1.0"},
            timeout=30,
        )
        if resp.ok:
            return resp.json().get("access_token")
        logger.error("Reddit auth failed: %s", resp.text[:200])
        return None
    except Exception as e:
        logger.error("Reddit auth error: %s", e)
        return None


def post(workspace_id: str, payload: dict) -> PostResult:
    token_data = get_active_token(workspace_id, "reddit")
    if not token_data:
        return PostResult(status="config_missing", channel="reddit", error="No Reddit token. Connect via /api/social/organic/config first.")

    # Interface compat: token_manager returns a bare access-token string (or None),
    # while tests mock it as a dict. Normalize to the dict shape used below.
    if isinstance(token_data, str):
        token_data = {"access_token": token_data}

    cfg = get_channel_config(workspace_id, "reddit")
    client_id = token_data.get("platform_user_id") or cfg.get("client_id", "")
    client_secret = cfg.get("client_secret", "")
    username = token_data.get("platform_username") or cfg.get("username", "")
    password = cfg.get("password", "")

    if not (client_id and client_secret and username and password):
        return PostResult(status="config_missing", channel="reddit", error="Reddit creds incomplete (client_id, client_secret, username, password).")

    access_token = _get_access_token(client_id, client_secret, username, password)
    if not access_token:
        return PostResult(status="error", channel="reddit", error="Reddit auth failed. Check credentials.")

    subreddit = payload["subreddit"].lstrip("r/")
    data = {"sr": subreddit, "title": payload["title"], "kind": "self", "text": payload["body"]}
    if payload.get("flair"):
        data["flair_id"] = payload["flair"]

    try:
        resp = requests.post(
            f"{REDDIT_API_URL}/api/submit",
            headers={"Authorization": f"bearer {access_token}", "User-Agent": "AgencyOrganicBot/1.0"},
            data=data,
            timeout=30,
        )
        if resp.ok:
            j = resp.json()
            post_id = ""
            if j.get("json", {}).get("data", {}).get("id"):
                post_id = j["json"]["data"]["id"]
            return PostResult(
                channel="reddit",
                post_id=post_id,
                post_url=f"https://www.reddit.com/r/{subreddit}/comments/{post_id}" if post_id else "",
            )
        return PostResult(status="error", channel="reddit", error=resp.text[:300])
    except Exception as e:
        return PostResult(status="error", channel="reddit", error=str(e)[:300])
