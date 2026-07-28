"""Test agent bus persistence."""
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


async def test_send_and_get_message():
    from admin.workspace.agent_bus import send_message, get_messages

    msg = send_message(
        from_agent="ceo",
        to_agent="seo",
        workspace_id="ws1",
        subject="Test brief",
        content="Do SEO audit",
    )
    assert msg.id is not None
    assert msg.subject == "Test brief"

    msgs = get_messages(workspace_id="ws1", to_agent="seo")
    assert len(msgs) >= 1
    assert msgs[0].subject == "Test brief"


async def test_share_and_get_knowledge():
    from admin.workspace.agent_bus import share_knowledge, get_knowledge, get_all_knowledge

    share_knowledge(
        workspace_id="ws1",
        key="keyword_strategy",
        value="Keyword clustering boosts rankings",
        source_agent="seo",
    )

    k = get_knowledge(workspace_id="ws1", key="keyword_strategy")
    assert len(k) >= 1
    assert "Keyword clustering" in k["keyword_strategy"]["value"]

    all_k = get_all_knowledge()
    assert len(all_k) >= 1


async def test_messages_unread_filter():
    from admin.workspace.agent_bus import send_message, get_messages, mark_read

    send_message("ceo", "content", "ws1", "Design brief", "Create 3 images")

    unread = get_messages(workspace_id="ws1", to_agent="content", unread_only=True)
    assert len(unread) >= 1

    mark_read(unread[0].id, workspace_id="ws1")

    unread_after = get_messages(workspace_id="ws1", to_agent="content", unread_only=True)
    msg_ids_after = {m.id for m in unread_after}
    assert unread[0].id not in msg_ids_after

