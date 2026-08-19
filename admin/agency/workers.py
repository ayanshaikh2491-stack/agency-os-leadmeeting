from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from admin.workspace.manager import append_agent_activity_log, update_agent_activity

WorkerFn = Callable[[str, dict], Awaitable[dict]]

WORKERS: dict[str, dict] = {}


def register_worker(worker_type: str, label: str, kind: str, fn: WorkerFn) -> None:
    WORKERS[worker_type] = {
        "type": worker_type,
        "label": label,
        "kind": kind,
        "runnable": fn,
    }


async def run_worker(worker: str, task: str, ctx: dict) -> dict:
    meta = WORKERS.get(worker)
    if meta is None:
        return {"ok": False, "error": f"unknown worker: {worker}"}

    scope = ctx.get("scope", {"kind": "agency", "workspace_id": "agency"})
    ws = scope.get("workspace_id", "agency")

    update_agent_activity(ws, worker, "working", task[:80])
    append_agent_activity_log(ws, worker, "task", f"CEO task: {task[:200]}")

    try:
        result: dict[str, Any] = await meta["runnable"](task, ctx)
    except Exception as exc:  # noqa: BLE001 - surface any worker failure
        update_agent_activity(ws, worker, "error")
        return {"ok": False, "error": str(exc)}

    update_agent_activity(ws, worker, "idle")
    append_agent_activity_log(ws, worker, "status", f"done: {task[:200]}")
    return {"ok": True, "result": result}


def list_workers() -> list[dict]:
    return [{"type": m["type"], "label": m["label"], "kind": m["kind"]} for m in WORKERS.values()]


async def _run_sba(task: str, ctx: dict) -> dict:
    from admin.agency.sba_autopilot import SBAAutopilot
    ap = SBAAutopilot()
    stats = await ap.run_once()
    return {"stats": stats}


async def _run_passthrough(task: str, ctx: dict) -> dict:
    # Specialist agents are invoked by the CEO via the existing /api routes.
    # Keep defensive until live-exec wiring lands in a later task.
    return {"note": f"{ctx.get('scope', {}).get('workspace_id', 'agency')}: {task[:120]}"}


def register_builtins() -> None:
    register_worker("sba", "SBA — Lead→Email→Meeting", "sales", _run_sba)
    register_worker("seo", "SEO", "growth", _run_passthrough)
    register_worker("website", "Website", "build", _run_passthrough)
    register_worker("ads", "Ads", "growth", _run_passthrough)
    register_worker("content", "Content", "creative", _run_passthrough)
    register_worker("social", "Social", "creative", _run_passthrough)
    register_worker("analytics", "Analytics", "insight", _run_passthrough)
