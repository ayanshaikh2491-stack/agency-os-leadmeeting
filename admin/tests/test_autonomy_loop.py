"""Autonomy loop tests — always-on agency loop + client delivery routing.

Verifies the control system that makes specialist agents self-scheduled (L2)
instead of waiting for a manual API tick, plus the SBA->CEO handoff auto-fire
and the client-facing agent endpoint routing.
"""
import sys

sys.path.insert(0, ".")


def test_agent_loop_module_imports():
    from admin.agency.agent_loop import (  # noqa: F401
        agent_loop_forever,
        agent_loop_tick,
        _run_due_tasks_safe,
        _auto_process_due_handoffs,
    )


def test_agent_loop_tick_runs_and_is_bounded():
    import asyncio
    from admin.agency import agent_loop as loop

    # With no due tasks and no handoffs, a tick should return cleanly (no raise,
    # no hang). Bounded by asyncio.wait_for in agent_loop_tick.
    result = asyncio.run(loop.agent_loop_tick())
    assert isinstance(result, dict)
    # Either it ran tasks or it had nothing due — both are valid clean states.
    assert "due_tasks" in result and "handoffs" in result


def test_agent_loop_autoprocesses_pending_handoff():
    """A booked lead's handoff (workspace_id=None) gets provisioned by the loop."""
    import asyncio
    from admin.agency import agent_loop as loop
    from admin.agency import orchestrator
    from admin.agency.sba_store import create_handoff, list_handoffs

    # Build a fake lead + handoff (handoff has workspace_id=None => unprocessed).
    lead = {
        "id": "test_lead_autoloop",
        "name": "Auto Loop Lead",
        "business_name": "AutoLoop Biz",
        "email": "auto@example.com",
        "phone": "000",
        "score": 80,
        "source": "test",
        "status": "new",
        "context": {"industry": "test", "needs": [], "scope": "", "next_steps": []},
        "meeting_ids": [],
    }
    from admin.agency import sba_store
    sba_store._leads[lead["id"]] = lead

    try:
        handoff = asyncio.run(create_handoff(lead["id"], "provision me"))
        assert handoff["workspace_id"] is None

        # The loop's auto-processor should spin up the workspace.
        out = asyncio.run(loop._auto_process_due_handoffs())
        assert out["checked"] >= 1
        assert any(h["handoff_id"] == handoff["id"] for h in out["processed"])

        # Re-check: the handoff is now provisioned.
        refreshed = list_handoffs(lead_id=lead["id"])
        assert refreshed and refreshed[0]["workspace_id"], "handoff should now have a workspace"
    finally:
        sba_store._leads.pop(lead["id"], None)
        sba_store._handoffs.pop(handoff["id"], None)


def test_client_agent_endpoint_allowlist_excludes_sba():
    """The client-facing endpoint must never expose SBA / email / meeting agents."""
    import admin.api.routes.store as store_routes

    allow = store_routes._CLIENT_AGENT_ALLOWLIST
    assert "sba" not in allow
    assert "ceo" not in allow
    assert "seo" in allow and "analyzing" in allow
