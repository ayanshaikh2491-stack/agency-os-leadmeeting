"""Test CEO LangGraph checkpointer wiring + conversation continuity."""
from __future__ import annotations

import sys
sys.path.insert(0, r"C:\Users\TAUSHEF\Downloads\int")

import pytest

pytestmark = pytest.mark.asyncio


class _StubGraph:
    """Fake compiled graph that records the invoke config."""

    def __init__(self) -> None:
        self.captured_thread: str | None = None

    async def ainvoke(self, state: dict, config: dict | None = None) -> dict:
        if config:
            self.captured_thread = config.get("configurable", {}).get("thread_id")
        return {"final_output": "CEO test response", "thinking_phases": []}


def _patch_context_builders(monkeypatch):
    monkeypatch.setattr("admin.agency.ceo._build_workspace_context", lambda: "")
    monkeypatch.setattr("admin.agency.ceo._build_handoff_context", lambda: "")
    monkeypatch.setattr("admin.agency.ceo._build_review_context", lambda: "")


async def test_build_ceo_graph_uses_agency_checkpointer(monkeypatch):
    from admin.agency import ceo
    from langgraph.checkpoint.memory import MemorySaver

    seen = {}

    def fake_get_checkpointer(workspace, agent):
        seen["workspace"] = workspace
        seen["agent"] = agent
        return MemorySaver()

    monkeypatch.setattr(ceo, "get_checkpointer", fake_get_checkpointer)
    graph = ceo.build_ceo_graph()
    assert graph is not None
    assert graph.checkpointer is not None
    assert seen == {"workspace": "Agency", "agent": "ceo"}


async def test_build_ceo_graph_accepts_explicit_checkpointer(monkeypatch):
    from admin.agency import ceo
    from langgraph.checkpoint.memory import MemorySaver

    mem = MemorySaver()
    graph = ceo.build_ceo_graph(checkpointer=mem)
    assert graph.checkpointer is mem


async def test_chat_uses_passed_conversation_id(monkeypatch):
    from admin.agency.ceo import AgencyCEO

    _patch_context_builders(monkeypatch)
    ceo_obj = AgencyCEO()
    stub = _StubGraph()
    ceo_obj.graph = stub  # type: ignore[assignment]

    response, conv_id, phases = await ceo_obj.chat(
        "Bhai, status kya hai?",
        conversation_id="conv-xyz-123",
    )
    assert conv_id == "conv-xyz-123"
    assert stub.captured_thread == "conv-xyz-123"
    assert response == "CEO test response"


async def test_chat_default_thread_when_no_id(monkeypatch):
    from admin.agency.ceo import AgencyCEO

    _patch_context_builders(monkeypatch)
    ceo_obj = AgencyCEO()
    stub = _StubGraph()
    ceo_obj.graph = stub  # type: ignore[assignment]

    _, conv_id, _ = await ceo_obj.chat("Hello")
    assert conv_id == "ceo_agency"
    assert stub.captured_thread == "ceo_agency"


async def test_chat_returns_error_message_on_graph_failure(monkeypatch):
    from admin.agency.ceo import AgencyCEO

    _patch_context_builders(monkeypatch)
    ceo_obj = AgencyCEO()

    class _BoomGraph:
        async def ainvoke(self, state, config=None):
            raise RuntimeError("boom")

    ceo_obj.graph = _BoomGraph()  # type: ignore[assignment]
    response, conv_id, phases = await ceo_obj.chat("test")
    assert "issue" in response
    assert conv_id == ""
