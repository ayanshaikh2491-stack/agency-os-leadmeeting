"""Ads Agent audit — converted to proper pytest tests.

Covers the three fixes from the ADS audit session:
  - ads_tools.py: missing `import random` (broke ad_copy_generator)
  - ads_tools.py: `(metrics or {}).get()` guard (broke campaign_report with None metrics)
  - agent_bus.py: sync-context `_fire_and_forget` (broke request_content outside a loop)
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, r"C:\Users\TAUSHEF\Downloads\int")

from admin.tools.ads_tools import ADS_TOOLS, execute_ads_tool
from admin.workspace.agents.ads import AdsAgent, build_ads_graph

ALL_TOOLS_AND_ARGS = [
    ("campaign_strategy", {"platform": "meta", "objective": "conversions"}),
    ("audience_research", {"industry": "fitness", "product": "yoga mat"}),
    ("budget_planner", {"total_budget": 50000, "duration_days": 30}),
    ("competitor_ads", {"competitors": ["BrandA", "BrandB"], "industry": "fitness"}),
    ("platform_selection", {"industry": "fitness", "goals": "B2C sales", "budget": 50000}),
    ("ad_copy_generator", {"product": "yoga mat", "platform": "meta", "tone": "bold"}),
    ("creative_brief", {"campaign_name": "Summer Sale", "product": "yoga mat", "platform": "meta"}),
    ("ad_variations", {"base_copy": "Best yoga mat ever", "platform": "meta", "count": 3}),
    ("landing_page_strategy", {"product": "yoga mat", "objective": "conversions"}),
    ("ad_hashtag_tags", {"product": "yoga mat", "platform": "meta", "niche": "fitness"}),
    ("audience_builder", {"age_min": 25, "age_max": 45, "interests": ["yoga", "fitness"]}),
    ("lookalike_audience", {"source_audience": "converters", "country": "IN"}),
    ("retargeting_setup", {"website_visitors_days": 30, "cart_abandoners": True}),
    ("exclusion_list", {"exclude_converters": True}),
    ("performance_analyzer", {"metrics": {"spend": 10000, "impressions": 500000, "clicks": 5000, "conversions": 50, "revenue": 25000}}),
    ("auto_optimize", {"rules": ["Pause if CPA > 2x target"]}),
    ("ab_test_setup", {"test_name": "Headline Test", "variable": "headline", "variants": ["A", "B"]}),
    ("campaign_report", {"campaign_name": "Summer Sale", "period": "30d"}),
    ("roas_calculator", {"ad_spend": 50000, "revenue": 200000, "target_roas": 4.0}),
    ("creative_score", {"creative_data": {"headline": "Best yoga mat", "has_cta": True, "has_social_proof": True, "has_urgency": True}}),
]

# campaign_report with metrics=None must not crash (fix 2)
NONE_METRICS_TOOLS = [("campaign_report", {"campaign_name": "Summer Sale", "period": "30d", "metrics": None})]


def test_imports():
    import admin.tools.ads_tools  # noqa: F401
    import admin.workspace.agents.ads  # noqa: F401
    import admin.api.routes.ads  # noqa: F401


def test_tool_count():
    assert len(ADS_TOOLS) == 20


@pytest.mark.parametrize("tool_name,args", ALL_TOOLS_AND_ARGS + NONE_METRICS_TOOLS)
def test_tool_executes(tool_name, args):
    result = execute_ads_tool(tool_name, args)
    assert "error" not in result, f"{tool_name} failed: {result}"


def test_graph_compiles():
    assert build_ads_graph() is not None


def test_agent_instantiation():
    agent = AdsAgent(workspace_name="Test", client_name="TestClient")
    assert agent.graph is not None
    assert agent._thread_id == "ads_Test"


def test_request_content_sends_brief():
    """Sync context (no running loop) — regression for fix 3."""
    agent = AdsAgent(workspace_name="Test", client_name="TestClient")
    result = agent.request_content(
        content_type="image",
        topic="Summer Sale Banner",
        platform="facebook",
        description="Bold summer sale banner for yoga mats",
        style="bold",
        priority="high",
        quantity=2,
    )
    assert result.get("status") == "brief_sent"


def test_skill_md_complete():
    skill_path = Path(r"C:\Users\TAUSHEF\Downloads\int\admin\skills\ads\SKILL.md")
    content = skill_path.read_text(encoding="utf-8")
    assert len(content.splitlines()) > 50
    assert "20 Real Tools" in content or "20 tools" in content
    assert "Q1" in content and "Q5" in content
    for t in ["campaign_strategy", "ad_copy_generator", "performance_analyzer", "roas_calculator"]:
        assert t in content


def test_main_registration():
    main_content = Path(r"C:\Users\TAUSHEF\Downloads\int\admin\main.py").read_text(encoding="utf-8")
    assert "ads as ads_routes" in main_content
    assert "ads_routes.router" in main_content
