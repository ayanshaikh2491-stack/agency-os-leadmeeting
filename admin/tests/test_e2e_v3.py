"""Phase 3 end-to-end test: persistence + CEO + retry + monitoring pipeline."""
from __future__ import annotations

import sys
sys.path.insert(0, r"C:\Users\TAUSHEF\Downloads\int")

import uuid
import pytest

pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
async def setup_db():
    from admin.persistence import init_persistence, close_persistence
    await init_persistence()
    yield
    await close_persistence()


async def test_e2e_full_pipeline():
    """End-to-end test covering create -> log -> monitor -> read."""
    from admin.api.models.schemas import WorkspaceCreate
    from admin.workspace.manager import create_workspace, route_to_agent
    from admin.workspace.manager import get_workspace
    from admin.ceo_data import log_activity, get_recent_activity
    from admin.agency.ceo_monitor import CEOMonitor

    ws_name = f"E2E Test {uuid.uuid4().hex[:8]}"
    ws = create_workspace(WorkspaceCreate(name=ws_name))
    assert ws is not None
    assert ws.name == ws_name
    assert ws.id is not None

    fetched = get_workspace(ws.id)
    assert fetched is not None, "Workspace must be accessible via get_workspace()"
    assert fetched.name == ws_name

    log_activity(
        agent_type="e2e_test_agent",
        action="test_action",
        workspace_id=ws.id,
        details="e2e_pipeline",
    )

    recent = get_recent_activity(limit=5)
    found = any(a.get("action") == "test_action" for a in recent)
    assert found, "Logged activity must appear in get_recent_activity()"

    monitor = CEOMonitor()
    status = await monitor.get_agency_status()
    assert isinstance(status, dict), "get_agency_status() must return a dict"
    assert "workspace_count" in status
    assert "alerts" in status
    assert "pending_reviews" in status

    result = await route_to_agent(
        workspace_id=ws.id,
        agent_type="nonexistent_agent",
        message="ping",
    )
    assert isinstance(result, str), "Unknown agent must return string, not crash"

    log_activity(
        agent_type="e2e_test_agent",
        action="e2e_complete",
        workspace_id=ws.id,
        details="e2e_complete",
    )

    recent2 = get_recent_activity(limit=10)
    actions = [a.get("action") for a in recent2]
    assert "e2e_complete" in actions, "All logged activities should be readable"
