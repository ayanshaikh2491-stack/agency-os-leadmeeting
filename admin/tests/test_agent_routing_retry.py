"""Test agent routing with retry logic."""
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


async def test_route_to_unknown_agent_graceful():
    """Unknown agent type should fail gracefully, not crash."""
    from admin.api.models.schemas import WorkspaceCreate
    from admin.workspace.manager import create_workspace, route_to_agent

    ws = create_workspace(WorkspaceCreate(name="Retry Test"))
    result = await route_to_agent(
        workspace_id=ws.id,
        agent_type="nonexistent_agent",
        message="Test",
    )
    assert isinstance(result, str)
    assert len(result) > 0


async def test_retry_function_can_be_imported():
    from admin.workspace.manager import _call_with_retry
    assert _call_with_retry is not None

