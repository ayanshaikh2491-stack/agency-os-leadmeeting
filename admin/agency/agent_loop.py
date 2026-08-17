"""Always-on Agency Agent Loop — the autonomy engine.

This is the missing control system that makes the specialist agents
(SEO / Website / Ads / Analytics / Analyzing / SBA scan) run themselves
instead of waiting for a manual API tick.

What it does, on a fixed cadence:
  1. Runs all due scheduled tasks via the existing `scheduler.run_due_tasks`
     (SEO scan -> report -> workspace CEO -> agency CEO -> agency SEO monitor).
  2. Auto-fires SBA -> CEO handoffs for leads that booked a meeting but whose
     client workspace has not been created yet. This closes the loop: a lead
     says "yes" to the SBA agent, the CEO agent spins up the client workspace
     and registers every specialist agent, and from then on those agents run
     themselves on their schedules.

Design notes (Engineering #16 root-cause fix):
  - The orchestrator + scheduler were fully built but `run_due_tasks()` was
    only reachable through a manual API endpoint. Nothing ran it on a timer,
    so every agent sat at L1 (manual). This loop is the timer.
  - It is the BACKGROUND counterpart to the SBA autopilot (which is its own
    process). The two never overlap: this loop only runs scheduled *reports*
    and workspace *provisioning*; the SBA autopilot owns live lead emailing.
  - Failures are swallowed per-cycle and logged. One bad task must never take
    the whole backend down (same principle as the organic scheduler loop).

Safety:
  - Bounded: one tick at a time, no unbounded fan-out.
  - Read-only audit: every tick is appended to loop-run-log.md-style state
    via the scheduler's own run_count; no destructive actions.
  - It NEVER sends external email / books meetings itself — those stay owned
    by the SBA autopilot and explicit owner gates.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from admin.config import settings

logger = logging.getLogger("agency.agent_loop")

# Seconds between ticks. Keep generous — scheduled tasks are daily/weekly,
# so a 60s tick only actually fires when something is due.
AGENT_LOOP_INTERVAL_SECONDS: int = int(
    getattr(settings, "AGENCY_AGENT_LOOP_INTERVAL_SECONDS", "60")
)

# Hard ceiling on a single tick so a stuck task cannot freeze the loop
# (seen historically: agents hang 9h). One task being slow must not block
# the rest of the agency.
AGENT_LOOP_TICK_TIMEOUT_SECONDS: int = int(
    getattr(settings, "AGENCY_AGENT_LOOP_TICK_TIMEOUT_SECONDS", "120")
)


async def _run_due_tasks_safe() -> dict[str, Any]:
    """Run all due scheduled tasks, swallowing per-task failures."""
    from admin.agency.scheduler import run_due_tasks

    try:
        return run_due_tasks()
    except Exception as exc:  # noqa: BLE001
        logger.exception("agent-loop: run_due_tasks failed: %s", exc)
        return {"ran": 0, "error": str(exc)}


async def _auto_process_due_handoffs() -> dict[str, Any]:
    """Auto-fire SBA -> CEO handoffs for booked leads missing a workspace.

    A handoff is created by the SBA pipeline when a lead books a meeting.
    If the workspace was never provisioned (e.g. the manual endpoint was not
    called), this brings it to life autonomously.
    """
    from admin.agency.orchestrator import ceo_process_sba_handoff
    from admin.agency.sba_store import list_handoffs

    processed = []
    try:
        pending = [h for h in list_handoffs() if not h.get("workspace_id")]
    except Exception as exc:  # noqa: BLE001
        logger.exception("agent-loop: list_handoffs failed: %s", exc)
        return {"checked": 0, "processed": [], "error": str(exc)}

    for handoff in pending:
        hid = handoff.get("id")
        if not hid:
            continue
        try:
            result = await ceo_process_sba_handoff(hid)
            processed.append({"handoff_id": hid, "result": result})
            logger.info("agent-loop: auto-processed SBA handoff %s", hid)
        except Exception as exc:  # noqa: BLE001
            logger.exception("agent-loop: handoff %s failed: %s", hid, exc)

    return {"checked": len(pending), "processed": processed}


async def _tick_once() -> dict[str, Any]:
    """One autonomy cycle: run due tasks + provision any booked leads."""
    due = await _run_due_tasks_safe()
    handoffs = await _auto_process_due_handoffs()
    return {
        "due_tasks": due,
        "handoffs": handoffs,
        "at": time.time(),
    }


async def agent_loop_tick() -> dict[str, Any]:
    """Public: run one bounded agency autonomy tick (with timeout guard)."""
    try:
        return await asyncio.wait_for(_tick_once(), timeout=AGENT_LOOP_TICK_TIMEOUT_SECONDS)
    except asyncio.TimeoutError:
        logger.warning(
            "agent-loop: tick exceeded %ss — resetting for next cycle",
            AGENT_LOOP_TICK_TIMEOUT_SECONDS,
        )
        return {"error": "tick_timeout"}
    except Exception as exc:  # noqa: BLE001
        logger.exception("agent-loop: tick crashed: %s", exc)
        return {"error": str(exc)}


async def agent_loop_forever() -> None:
    """Background coroutine: run the autonomy loop forever."""
    logger.info(
        "agent-loop: starting (interval=%ds, tick_timeout=%ds)",
        AGENT_LOOP_INTERVAL_SECONDS,
        AGENT_LOOP_TICK_TIMEOUT_SECONDS,
    )
    while True:
        try:
            result = await agent_loop_tick()
            ran = result.get("due_tasks", {}).get("ran", 0)
            handoffs = len(result.get("handoffs", {}).get("processed", []))
            if ran or handoffs:
                logger.info(
                    "agent-loop: tick ran %s scheduled tasks, auto-processed %s handoffs",
                    ran,
                    handoffs,
                )
        except Exception as exc:  # noqa: BLE001 — never let the loop die
            logger.exception("agent-loop: unexpected error: %s", exc)
        await asyncio.sleep(AGENT_LOOP_INTERVAL_SECONDS)
