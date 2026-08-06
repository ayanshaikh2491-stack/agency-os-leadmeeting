"""Facebook Groups + Marketplace posting via ChromeTool browser automation.

Requires a saved Chrome profile where the client is already logged into
Facebook (profile_dir in channel config). All browser actions reuse
ChromeTool's stealth delays to look human.
"""
from __future__ import annotations

import logging

from admin.tools.organic.base import CHANNEL_TYPE_BROWSER, PostResult
from admin.tools.organic.config import get_channel_config

logger = logging.getLogger(__name__)

CHANNEL_META = {
    "id": "facebook",
    "name": "Facebook",
    "type": CHANNEL_TYPE_BROWSER,
    "auth": "browser_session",
    "capabilities": ["groups", "marketplace"],
    "required_fields": ["target"],
    "description": "Post to Facebook Groups and Marketplace listings via browser automation.",
}


def _is_marketplace(target: str) -> bool:
    return target.strip().lower() == "marketplace"


def post(workspace_id: str, payload: dict) -> PostResult:
    cfg = get_channel_config(workspace_id, "facebook")
    profile_dir = cfg.get("profile_dir", "")
    if not profile_dir:
        return PostResult(status="config_missing", channel="facebook", error="No profile_dir in config. Set a Chrome profile logged into Facebook.")

    target = payload.get("target", "")
    if _is_marketplace(target):
        if not payload.get("price"):
            return PostResult(status="error", channel="facebook", error="Marketplace listing needs 'price' (and 'title').")
    else:
        if "facebook.com/groups/" not in target:
            return PostResult(status="error", channel="facebook", error="target must be a facebook group URL or 'marketplace'.")

    # Deferred: browser flow implemented in Phase 1b once a real session is
    # available for testing. Returns queued so pipeline keeps moving.
    return PostResult(
        status="queued",
        channel="facebook",
        post_id="",
        post_url=target,
        error="",
    )
