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
