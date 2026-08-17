"""Tests for the structured multi-agent communication bus (agent_bus.py).

Verifies doc #24 requirements: structured messages (sender/receiver/workspace/
task/status), workspace isolation (#25), persistence across reopen (#21), and
the brief/respond/parallel_blast/share_knowledge API.
"""

import sqlite3

import os
import pytest

from admin.agency.agent_bus import AgentBus, get_bus, _VALID_STATUSES


@pytest.fixture()
def bus():
    """Fresh bus in an isolated file under the repo (Windows %TEMP% hangs here)."""
    d = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "_bus_test_dir")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, f"bus_{os.getpid()}.db")
    b = AgentBus(p)
    try:
        yield b
    finally:
        b.close()
        if os.path.exists(p):
            try:
                os.remove(p)
            except OSError:
                pass


def test_brief_returns_id_and_stores(bus):
    mid = bus.brief("ceo", "sba", "agency", "find_leads",
                    objective="get 10 local dentists", context="Miami")
    msg = bus.thread(mid)
    assert msg is not None
    assert msg.sender == "ceo" and msg.receiver == "sba" and msg.workspace == "agency"
    assert msg.task == "find_leads"
    assert msg.status == "pending"
    assert msg.objective == "get 10 local dentists"


def test_respond_updates_status_and_result(bus):
    mid = bus.brief("ceo", "sba", "agency", "research")
    updated = bus.respond(mid, result="found 12 leads", status="done")
    assert updated is not None
    assert updated.status == "done"
    assert updated.result == "found 12 leads"
    # thread reflects the update
    assert bus.thread(mid).status == "done"


def test_respond_unknown_id_returns_none(bus):
    assert bus.respond("nope") is None


def test_invalid_status_rejected(bus):
    with pytest.raises(ValueError):
        bus.brief("ceo", "sba", "agency", "x", status="banana")
    with pytest.raises(ValueError):
        bus.respond(bus.brief("ceo", "sba", "agency", "x"), status="wat")


def test_workspace_isolation(bus):
    bus.brief("ceo", "sba", "agency", "t1")
    bus.brief("ceo", "sba", "clientX", "t2")
    inbox_agency = bus.inbox("sba", "agency")
    assert len(inbox_agency) == 1
    assert inbox_agency[0].workspace == "agency"
    assert len(bus.inbox("sba", "clientX")) == 1


def test_parallel_blast_multi_receiver(bus):
    ids = bus.parallel_blast("ceo", "agency", ["sba", "seo", "ads"], "quarterly_plan")
    assert len(ids) == 3
    assert len(bus.inbox("sba", "agency")) == 1
    assert len(bus.inbox("seo", "agency")) == 1
    assert len(bus.inbox("ads", "agency")) == 1


def test_share_knowledge_stored_and_queryable(bus):
    bus.share_knowledge("sba", "agency", "best_industry", {"industry": "dentist"})
    rows = bus.knowledge("agency", topic="best_industry")
    assert len(rows) == 1
    assert rows[0]["sender"] == "sba"
    # also appears as a broadcast message
    assert any(m.receiver == "broadcast" for m in bus.recent("agency", limit=10))


def test_persistence_across_reopen(tmp_path):
    """Messages survive a bus reopen (doc #21)."""
    path = str(tmp_path / "persist.db")
    b1 = AgentBus(path)
    mid = b1.brief("ceo", "sba", "agency", "persist_me")
    b1.close()

    b2 = AgentBus(path)  # simulate restart
    msg = b2.thread(mid)
    assert msg is not None and msg.status == "pending"
    b2.close()


def test_get_bus_singleton():
    """get_bus returns a cached singleton (no duplicate connections)."""
    import admin.agency.agent_bus as mod
    d = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "_bus_test_dir")
    os.makedirs(d, exist_ok=True)
    db = os.path.join(d, f"global_{os.getpid()}.db")
    a = mod.get_bus(db)
    b = mod.get_bus()
    try:
        assert a is b
    finally:
        a.close()
        mod._bus_singleton = None  # reset so no real agent_bus.db lingers
