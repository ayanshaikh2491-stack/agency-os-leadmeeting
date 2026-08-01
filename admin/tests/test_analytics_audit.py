"""Analytics Agent audit — converted to proper pytest tests."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, r"C:\Users\TAUSHEF\Downloads\int")

from admin.tools.analytics_tools import ANALYTICS_TOOLS, execute_analytics_tool
from admin.workspace.agents.analytics import AnalyticsAgent, build_analytics_graph

ALL_TOOLS_AND_ARGS = [
    ("weekly_report", {"workspace": "Test", "client": "TestClient"}),
    ("monthly_report", {"workspace": "Test", "client": "TestClient"}),
    ("campaign_report", {"campaign_name": "Summer Sale", "platform": "meta"}),
    ("custom_report", {"focus_areas": ["traffic", "conversions"]}),
    ("track_traffic", {"channel": "all", "period": "last 7 days"}),
    ("track_rankings", {"keywords": ["digital marketing", "seo services"]}),
    ("track_conversions", {"channel": "ads", "period": "last 7 days"}),
    ("track_revenue", {"period": "last 30 days", "channel": "all"}),
    ("cross_channel_analysis", {"workspace": "Test", "channels": ["seo", "ads"]}),
    ("roi_calculator", {"channel": "ads", "spend": 50000, "revenue": 200000}),
    ("funnel_analysis", {"workspace": "Test", "funnel_type": "website"}),
    ("competitor_benchmark", {"competitors": ["Comp A", "Comp B"]}),
    ("anomaly_detector", {"metric": "traffic", "current_value": 5000, "expected_value": 10000}),
    ("threshold_alert", {"metric": "roas", "current_value": 2.5, "threshold_min": 3.0}),
    ("competitor_alert", {"competitor": "Comp A", "change_type": "traffic_spike"}),
    ("traffic_forecast", {"channel": "all", "months": 3, "current_traffic": 10000}),
    ("budget_forecast", {"current_spend": 50000, "target_roas": 4.0, "months": 3}),
    ("growth_projection", {"metric": "revenue", "current_value": 100000, "target_value": 300000}),
    ("data_aggregator", {"workspace": "Test", "channels": ["seo", "ads", "social"]}),
    ("email_report", {"to": ["test@example.com"], "report_type": "weekly", "workspace": "Test"}),
]


def test_imports():
    import admin.tools.analytics_tools  # noqa: F401
    import admin.workspace.agents.analytics  # noqa: F401
    import admin.api.routes.analytics  # noqa: F401
    import admin.utils.email_sender  # noqa: F401


def test_tool_count():
    assert len(ANALYTICS_TOOLS) == 20


@pytest.mark.parametrize("tool_name,args", ALL_TOOLS_AND_ARGS)
def test_tool_executes(tool_name, args):
    result = execute_analytics_tool(tool_name, args)
    assert "error" not in result, f"{tool_name} failed: {result}"


def test_graph_compiles():
    assert build_analytics_graph() is not None


def test_agent_instantiation():
    agent = AnalyticsAgent(workspace_name="Test", client_name="TestClient")
    assert agent.graph is not None
    assert agent._thread_id == "analytics_Test"


def test_email_functions_exist():
    from admin.utils.email_sender import send_email, send_report_email, send_alert_email

    assert callable(send_email)
    assert callable(send_report_email)
    assert callable(send_alert_email)


def test_skill_md_complete():
    skill_path = Path(r"C:\Users\TAUSHEF\Downloads\int\admin\skills\analytics\SKILL.md")
    content = skill_path.read_text(encoding="utf-8")
    assert len(content.splitlines()) > 50
    assert "20 Real Tools" in content or "20 tools" in content
    assert "email" in content.lower()
    for t in ["weekly_report", "monthly_report", "track_traffic", "anomaly_detector", "email_report"]:
        assert t in content


def test_main_registration():
    main_content = Path(r"C:\Users\TAUSHEF\Downloads\int\admin\main.py").read_text(encoding="utf-8")
    assert "analytics as analytics_routes" in main_content
    assert "analytics_routes.router" in main_content
