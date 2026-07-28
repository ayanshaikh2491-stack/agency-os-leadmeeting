"""Test workspace manager persistence."""
from __future__ import annotations

import sys
sys.path.insert(0, r"C:\Users\TAUSHEF\Downloads\int")

import pytest
from admin.api.models.schemas import WorkspaceCreate

pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
async def setup_db():
    from admin.persistence import init_persistence, close_persistence
    await init_persistence()
    yield
    await close_persistence()


async def test_create_workspace_persists():
    from admin.workspace.manager import create_workspace, get_workspace, list_workspaces

    ws = create_workspace(WorkspaceCreate(
        name="Test Co",
        client_name="Test Client",
        description="Testing persistence",
    ))
    assert ws.id is not None
    assert ws.name == "Test Co"

    fetched = get_workspace(ws.id)
    assert fetched is not None
    assert fetched.name == "Test Co"

    all_ws = list_workspaces()
    assert any(w.id == ws.id for w in all_ws)


async def test_agent_output_stored():
    from admin.workspace.manager import create_workspace, store_agent_output, list_pending_reviews

    ws = create_workspace(WorkspaceCreate(name="Output Test"))

    store_agent_output(
        workspace_id=ws.id,
        agent_type="seo",
        task="Audit site",
        output="Site audit complete. Score: 65/100.",
    )

    pending = list_pending_reviews()
    assert any(r["workspace_id"] == ws.id for r in pending)


async def test_review_stored():
    from admin.workspace.manager import store_agent_output, store_review, list_reviews, create_workspace

    ws = create_workspace(WorkspaceCreate(name="Review Test"))
    out = store_agent_output(ws.id, "seo", "Task", "Output")

    store_review(
        workspace_id=ws.id,
        agent_type="seo",
        output_id=out["id"],
        verdict="approved",
        feedback="Good work",
    )

    reviews = list_reviews(ws.id)
    assert len(reviews) >= 1
    assert reviews[0]["verdict"] == "approved"


async def test_error_log_stored():
    from admin.workspace.manager import store_error, list_errors, create_workspace

    ws = create_workspace(WorkspaceCreate(name="Error Test"))
    store_error(ws.id, "seo_issue", "high", "Rankings dropped", routed_to="seo")

    errors = list_errors(ws.id)
    assert len(errors) >= 1
    assert errors[0]["error_type"] == "seo_issue"
