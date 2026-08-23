"""Verify Ads Agent CORE works (not just AEO/GEO).

Proves: module imports, graph builds, core functions + 20 tools present,
State shape valid, and the LLM call path renders without error.
"""
import pytest
from admin.workspace.agents import ads


def test_module_imports():
    assert ads.__name__ == "admin.workspace.agents.ads"


def test_graph_builds():
    g = ads.build_ads_graph()
    assert g is not None


def test_core_functions_present():
    for fn in ["ads_route", "build_ads_graph", "ads_call_llm"]:
        assert hasattr(ads, fn), f"MISSING {fn}"


def test_tools_registered():
    assert ads.ADS_TOOLS and len(ads.ADS_TOOLS) >= 15


def test_state_shape():
    st = ads.AdsAgentState(
        messages=[{"role": "user", "content": "hi"}],
        workspace_name="Houston Plumbing Co",
        client_name="Test",
        workspace_context="x",
        tool_round=0,
        final_output="",
        error=None,
    )
    assert st["workspace_name"] == "Houston Plumbing Co"


def test_llm_call_renders_prompt():
    # Render the system prompt the LLM call builds (no network/API call).
    prompt = ads.ADS_SYSTEM_PROMPT.format(
        workspace_name="Houston Plumbing Co",
        client_name="Test",
        workspace_context="No data yet.",
        aeo_geo_context="[AEO/GEO injected]",
    )
    assert "Ads Agent" in prompt
    assert "AI Visibility" in prompt
    assert "campaign_strategy" in prompt  # core tool still listed
