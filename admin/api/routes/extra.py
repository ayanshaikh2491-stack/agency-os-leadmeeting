"""Extra API Routes — status + social tokens for the Next.js frontend.

Endpoints:
  GET /api/status                — Agency pipeline summary (dashboard)
  GET /api/social/tokens/status  — Connected social platform accounts
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(tags=["extra"])


@router.get("/api/status", tags=["system"])
async def api_status() -> dict[str, Any]:
    """Agency status — pipeline summary + workspace count.

    Shape matches what the frontend expects:
      status?.pipeline?.queue?.total / .new / .leads_found_today
    """
    from admin.agency.sba_store import list_leads
    from admin.workspace.manager import list_workspaces

    all_leads = list_leads()
    by_status: dict[str, int] = {}
    for s in ["new", "contacted", "meeting", "proposal", "negotiation", "closed", "lost"]:
        by_status[s] = len([l for l in all_leads if l["status"] == s])

    new_count = by_status.get("new", 0)
    total_in_pipeline = sum(by_status.values())
    hot_leads = len([l for l in all_leads if l.get("score", 0) >= 80 and l["status"] != "closed"])

    try:
        workspace_count = len(list_workspaces())
    except Exception:  # noqa: BLE001
        workspace_count = 0

    return {
        "success": True,
        "pipeline": {
            "leads_found_today": new_count,
            "queue": {"total": total_in_pipeline, "new": new_count},
            "by_status": by_status,
            "hot_leads": hot_leads,
        },
        "workspaces": workspace_count,
    }


@router.get("/api/social/tokens/status")
async def social_tokens_status() -> dict[str, Any]:
    """Return connected social accounts.

    The frontend reads `connected_accounts[].platform` to render the
    connected-platforms strip on agent pages. Currently no OAuth tokens are
    stored on this backend, so the list is empty (frontend handles that
    gracefully and shows no connected platforms).
    """
    return {
        "success": True,
        "connected_accounts": [],
        "platforms": [],
    }
