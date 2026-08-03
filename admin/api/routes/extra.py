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


# ── Agent status (frontend polls /api/agents/{slug}/status) ────────────────

_AGENT_STATUS_KEYS = {
    "seo-engine": "seo",
    "website-builder": "website",
    "social-manager": "social",
    "content-creator": "content",
    "ads-runner": "ads",
    "analytics-bot": "analytics",
    "client-success": "client_success",
    "intake-researcher": "intake",
    "review-qc": "review",
    "sales-closer": "sales",
}


@router.get("/api/agents/{agent_id}/status")
async def api_agent_status(agent_id: str) -> dict[str, Any]:
    """Agent status used by the agent pages' mount check.

    The agent pages call GET /api/agents/{slug}/status and treat the agent as
    online when `success && <slug-key>.status === 'running'`. This backend is
    the live orchestration layer, so all registered agents are reported as
    running (they proxy to this backend for chat/actions).
    """
    key = _AGENT_STATUS_KEYS.get(agent_id, agent_id.replace("-", "_"))
    return {
        "success": True,
        "agent_id": agent_id,
        key: {"status": "running"},
    }


# ── Workspace aliases (frontend uses /api/workspaces, backend CRUD is
#    /api/chat/workspace). Kept here so the Next.js catch-all proxy
#    (/api/workspaces/...) reaches a live backend route. ────────────────────


def _ws_item(ws: Any) -> dict[str, Any]:
    dump = getattr(ws, "model_dump", None)
    if callable(dump):
        return dump(mode="json")
    return dict(ws)


@router.get("/api/workspaces")
async def api_workspaces() -> dict[str, Any]:
    from admin.workspace.manager import list_workspaces

    items = [_ws_item(w) for w in list_workspaces()]
    return {"success": True, "workspaces": items, "data": {"workspaces": items}}


@router.post("/api/workspaces")
async def api_workspaces_create(payload: dict[str, Any]) -> dict[str, Any]:
    from admin.api.models.schemas import WorkspaceCreate
    from admin.workspace.manager import create_workspace

    wc = WorkspaceCreate(
        name=(payload.get("name") or "").strip(),
        client_name=payload.get("client_name") or payload.get("name") or "",
        description=payload.get("description") or payload.get("industry") or "",
    )
    item = _ws_item(create_workspace(wc))
    return {"success": True, "workspace": item, "data": {"workspace": item}}


@router.get("/api/workspaces/{ws_id}/sba")
async def api_workspace_sba(ws_id: str) -> dict[str, Any]:
    from admin.workspace.manager import get_workspace

    ws = get_workspace(ws_id)
    if not ws:
        return {"success": False, "error": "Workspace not found"}
    return {"success": True, "data": _ws_item(ws)}


@router.delete("/api/workspaces/{ws_id}")
async def api_workspace_delete(ws_id: str) -> dict[str, Any]:
    from admin.workspace.manager import delete_workspace

    ok = delete_workspace(ws_id)
    return {"success": ok, "deleted": ok}
