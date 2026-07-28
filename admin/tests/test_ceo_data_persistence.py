"""Test CEO data layer persistence."""
from __future__ import annotations

import sys
sys.path.insert(0, r"C:\Users\TAUSHEF\Downloads\int")

import pytest

pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
async def setup_db():
    from admin.persistence import init_persistence, close_persistence
    await init_persistence()
    yield
    await close_persistence()


async def test_log_and_get_activity():
    from admin.ceo_data import log_activity, get_recent_activity

    log_activity(
        workspace_id="ws1",
        agent_type="ceo",
        action="delegated_task",
        details="Sent SEO audit request",
        metadata={"priority": "high"},
    )

    activity = get_recent_activity(limit=10)
    assert len(activity) >= 1
    assert activity[0]["action"] == "delegated_task"


async def test_get_agency_overview():
    from admin.ceo_data import get_agency_overview

    overview = get_agency_overview()
    assert "workspaces" in overview
    assert "summary" in overview
    assert "alerts" in overview
    assert overview["summary"]["total_workspaces"] >= 0


async def test_get_workspace_health():
    from admin.ceo_data import get_workspace_health

    health = get_workspace_health("nonexistent")
    assert "error" in health or "workspace" in health

