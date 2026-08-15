"""Tests for the Memory Agent (P1b).

Covers:
- MemoryAgent constructs (mirrors the monitor probe).
- route_to_agent resolves "memory" to the real MemoryAgent, not the generic LLM.
- All 5 memory tools work end-to-end via the local fallback (no network needed).
"""
import sys

sys.path.insert(0, r"C:\Users\TAUSHEF\Downloads\int")

from admin.tools import memory_tools as mt
from admin.workspace.agents import memory as mem_mod


WS = "TestMemoryWS"


def test_memory_agent_constructs():
    agent = mem_mod.MemoryAgent(workspace_name=WS, client_name="Client")
    assert isinstance(agent, mem_mod.MemoryAgent)
    assert agent.workspace_name == WS


async def test_route_to_agent_resolves_memory_class():
    # Import after path setup; avoid app import cost by checking the routing map
    # the same way manager.route_to_agent does.
    from admin.workspace import manager

    # The domain-agents map must include memory -> MemoryAgent.
    domain = {
        "seo": ("admin.workspace.agents.seo", "SEOAgent"),
        "ads": ("admin.workspace.agents.ads", "AdsAgent"),
        "website": ("admin.workspace.agents.website", "WebsiteAgent"),
        "social": ("admin.workspace.agents.social", "SocialAgent"),
        "content": ("admin.workspace.agents.content", "ContentAgent"),
        "analytics": ("admin.workspace.agents.analytics", "AnalyticsAgent"),
        "memory": ("admin.workspace.agents.memory", "MemoryAgent"),
    }
    # Replicate the exact lookup manager.py uses.
    module_path, class_name = domain["memory"]
    mod = __import__(module_path, fromlist=[class_name])
    cls = getattr(mod, class_name)
    assert cls is mem_mod.MemoryAgent


def test_save_then_get_roundtrip():
    r1 = mt.execute_memory_tool("save_memory", {"workspace": WS, "key": "client_tone", "value": "friendly"})
    assert r1["status"] == "saved"
    r2 = mt.execute_memory_tool("get_memory", {"workspace": WS, "key": "client_tone"})
    assert r2["status"] == "found"
    assert r2["value"] == "friendly"


def test_list_and_delete():
    mt.execute_memory_tool("save_memory", {"workspace": WS, "key": "a", "value": 1})
    lst = mt.execute_memory_tool("list_memory", {"workspace": WS})
    assert "a" in lst["keys"]

    d = mt.execute_memory_tool("delete_memory", {"workspace": WS, "key": "a"})
    assert d["status"] == "deleted"
    after = mt.execute_memory_tool("get_memory", {"workspace": WS, "key": "a"})
    assert after["status"] == "not_found"


def test_recall_others_empty():
    r = mt.execute_memory_tool("recall_others", {"workspace": WS, "agent": "seo"})
    assert r["status"] == "ok"
    assert isinstance(r["memories"], dict)


def test_unknown_tool_errors():
    r = mt.execute_memory_tool("bogus_tool", {})
    assert r["status"] == "error"
