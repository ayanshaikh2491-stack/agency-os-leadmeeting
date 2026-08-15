"""Tests for the agency-wide AgentHealthMonitor.

Run: pytest admin/tests/test_agent_monitor.py
"""
import sys

sys.path.insert(0, r"C:\Users\TAUSHEF\Downloads\int")

from admin.agency import agent_monitor as am


def test_probe_healthy_agent_imports():
    # SEO agent has a real module + class; construction should succeed.
    rec = am.probe_agent("seo", am._AGENT_PROBES["seo"])
    assert rec["status"] == "healthy", rec
    assert rec["error"] is None


def test_probe_content_agent_constructs():
    rec = am.probe_agent("content", am._AGENT_PROBES["content"])
    assert rec["status"] == "healthy", rec


def test_probe_memory_agent_constructs():
    # P1b: admin.workspace.agents.memory now exists (real MemoryAgent).
    rec = am.probe_agent("memory", am._AGENT_PROBES["memory"])
    assert rec["status"] == "healthy", rec
    assert rec["error"] is None


def test_monitor_all_agents_healthy():
    import asyncio

    mon = am.AgentHealthMonitor()
    health = asyncio.run(mon.get_health())
    assert "agents" in health
    # Every registered agent (incl. memory) must construct cleanly.
    assert health["all_healthy"] is True, health["agents"]
    assert health["down_count"] == 0
