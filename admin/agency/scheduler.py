"""Agent Scheduler — daily/weekly auto-run tasks.

Manages scheduled tasks that run automatically:
  - Daily: onpage check, rank tracking
  - Weekly: site audit, keyword research, report generation
  - Monthly: full audit, schema check

Uses in-memory scheduling (no external dependencies).
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any

logger = logging.getLogger(__name__)


# In-memory schedule store
_schedules: dict[str, dict[str, Any]] = {}
# schedule_id -> {
#   id, workspace_id, task_type, params,
#   frequency: "daily"|"weekly"|"monthly",
#   next_run: ISO string, last_run: ISO string,
#   enabled: bool, created_at
# }


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_str() -> str:
    return _now().isoformat()


def _new_id() -> str:
    return uuid.uuid4().hex[:10]


# ═══════════════════════════════════════════════════════════════════════════════
# SCHEDULE CRUD
# ═══════════════════════════════════════════════════════════════════════════════

def create_schedule(
    workspace_id: str,
    task_type: str,
    params: dict[str, Any] | None = None,
    frequency: str = "daily",
    enabled: bool = True,
) -> dict[str, Any]:
    """Create a scheduled task."""
    sid = _new_id()
    now = _now()

    if frequency == "daily":
        next_run = now + timedelta(hours=24)
    elif frequency == "weekly":
        next_run = now + timedelta(days=7)
    elif frequency == "monthly":
        next_run = now + timedelta(days=30)
    else:
        next_run = now + timedelta(hours=24)

    schedule = {
        "id": sid,
        "workspace_id": workspace_id,
        "task_type": task_type,
        "params": params or {},
        "frequency": frequency,
        "enabled": enabled,
        "next_run": next_run.isoformat(),
        "last_run": None,
        "run_count": 0,
        "created_at": _now_str(),
    }
    _schedules[sid] = schedule
    logger.info("Created schedule: %s/%s every %s", workspace_id, task_type, frequency)
    return schedule


def get_schedules(workspace_id: str | None = None) -> list[dict[str, Any]]:
    schedules = list(_schedules.values())
    if workspace_id:
        schedules = [s for s in schedules if s["workspace_id"] == workspace_id]
    return sorted(schedules, key=lambda s: s["next_run"])


def delete_schedule(schedule_id: str) -> bool:
    return _schedules.pop(schedule_id, None) is not None


def toggle_schedule(schedule_id: str, enabled: bool) -> dict[str, Any] | None:
    s = _schedules.get(schedule_id)
    if not s:
        return None
    s["enabled"] = enabled
    return s


# ═══════════════════════════════════════════════════════════════════════════════
# SCHEDULER ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

def get_due_tasks() -> list[dict[str, Any]]:
    """Get all tasks that are due to run now."""
    now = _now_str()
    due = []
    for s in _schedules.values():
        if s["enabled"] and s["next_run"] <= now:
            due.append(s)
    return due


def run_due_tasks() -> dict[str, Any]:
    """Run all due scheduled tasks.

    This is the main scheduler tick. Call it periodically (e.g., every minute).
    """
    due = get_due_tasks()
    if not due:
        return {"message": "No tasks due", "ran": 0}

    results = []
    for schedule in due:
        task_type = schedule["task_type"]
        workspace_id = schedule["workspace_id"]
        params = schedule["params"]

        logger.info("Running scheduled task: %s for workspace %s", task_type, workspace_id)

        try:
            if task_type == "seo_scan":
                from admin.agency.orchestrator import run_seo_agent_for_workspace
                result = run_seo_agent_for_workspace(workspace_id)
            elif task_type == "agency_seo_monitor":
                from admin.agency.orchestrator import agency_seo_monitor
                result = agency_seo_monitor()
            elif task_type == "workspace_ceo_to_agency":
                from admin.agency.orchestrator import workspace_ceo_to_agency_ceo
                result = workspace_ceo_to_agency_ceo(workspace_id)
            else:
                from admin.tools.seo_tools import execute_seo_tool
                result = execute_seo_tool(task_type, params)

            results.append({
                "schedule_id": schedule["id"],
                "task_type": task_type,
                "workspace_id": workspace_id,
                "status": "success",
                "result": result,
            })
        except Exception as e:
            results.append({
                "schedule_id": schedule["id"],
                "task_type": task_type,
                "workspace_id": workspace_id,
                "status": "failed",
                "error": str(e),
            })
            logger.exception("Scheduled task failed: %s", task_type)

        # Update next_run
        schedule["last_run"] = _now_str()
        schedule["run_count"] += 1
        now = _now()
        if schedule["frequency"] == "daily":
            schedule["next_run"] = (now + timedelta(hours=24)).isoformat()
        elif schedule["frequency"] == "weekly":
            schedule["next_run"] = (now + timedelta(days=7)).isoformat()
        elif schedule["frequency"] == "monthly":
            schedule["next_run"] = (now + timedelta(days=30)).isoformat()

    return {
        "message": f"Ran {len(results)} tasks",
        "ran": len(results),
        "results": results,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# AUTO-SETUP: Default schedules for a client workspace
# ═══════════════════════════════════════════════════════════════════════════════

def setup_default_schedules(workspace_id: str) -> list[dict[str, Any]]:
    """Create default daily/weekly schedules for a client workspace."""
    schedules = []

    # Daily: onpage check
    schedules.append(create_schedule(
        workspace_id, "onpage_check",
        params={"url": _get_target_url(workspace_id)},
        frequency="daily",
    ))

    # Daily: track rankings (if keywords set)
    kw = _get_keywords(workspace_id)
    if kw:
        for keyword in kw[:3]:
            schedules.append(create_schedule(
                workspace_id, "track_rankings",
                params={"keyword": keyword, "target_url": _get_target_url(workspace_id)},
                frequency="daily",
            ))

    # Weekly: site audit
    schedules.append(create_schedule(
        workspace_id, "site_audit",
        params={"url": _get_target_url(workspace_id), "max_pages": 5},
        frequency="weekly",
    ))

    # Weekly: keyword research
    if kw:
        schedules.append(create_schedule(
            workspace_id, "keyword_research",
            params={"seed_keyword": kw[0]},
            frequency="weekly",
        ))

    # Weekly: generate report
    schedules.append(create_schedule(
        workspace_id, "generate_report",
        params={"url": _get_target_url(workspace_id), "keywords": kw},
        frequency="weekly",
    ))

    # Daily: SEO scan + report up chain
    schedules.append(create_schedule(
        workspace_id, "seo_scan",
        params={},
        frequency="daily",
    ))

    return schedules


def setup_agency_schedules() -> list[dict[str, Any]]:
    """Create agency-level schedules (monitor quality)."""
    schedules = []

    # Daily: Agency SEO monitors all client reports
    schedules.append(create_schedule(
        "agency", "agency_seo_monitor",
        params={},
        frequency="daily",
    ))

    return schedules


def _get_target_url(workspace_id: str) -> str:
    from admin.agency.orchestrator import get_workspace
    ws = get_workspace(workspace_id)
    if ws:
        return ws.get("settings", {}).get("target_url", "https://example.com")
    return "https://example.com"


def _get_keywords(workspace_id: str) -> list[str]:
    from admin.agency.orchestrator import get_workspace
    ws = get_workspace(workspace_id)
    if ws:
        return ws.get("settings", {}).get("keywords", [])
    return []
