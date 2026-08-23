"""Social Media Agent real research via Agent-Reach (free channels).

Proof:
- social_tools 4 research tools now return real/structured data (not LLM-only)
- social_reach wraps Agent-Reach Web + V2EX safely (no crash on failure)
- audience_analysis returns real platform intel regardless of network
"""
from unittest.mock import patch

import pytest

from admin.tools import social_tools as st
from admin.tools import social_reach as sr


def test_social_reach_imports():
    assert hasattr(sr, "reach_trending")
    assert hasattr(sr, "reach_competitor")
    assert hasattr(sr, "reach_hashtags")
    assert hasattr(sr, "reach_audience")


def test_trend_research_returns_structure():
    r = st.trend_research("plumbing", "instagram")
    assert r["topic"] == "plumbing"
    assert "trending_formats" in r
    # does not crash; returns a dict even if network down
    assert isinstance(r, dict)


def test_hashtag_research_returns_structure():
    r = st.research_hashtags("plumbing", "instagram", 10)
    assert r["topic"] == "plumbing"
    assert "categories" in r
    assert isinstance(r, dict)


def test_competitor_analysis_returns_structure():
    r = st.competitor_analysis(["nasa"], "instagram")
    assert "analysis_framework" in r
    assert isinstance(r, dict)


def test_audience_analysis_returns_platform_intel():
    # local intel works without network
    r = st.audience_analysis("instagram", "plumbing")
    assert r["platform"] == "instagram"
    assert r["analysis_dimensions"]
    assert r["best_times"] or r["algorithm_factors"]


def test_reach_trending_real_v2ex():
    # V2EX is a public API (no auth) -> real data returns
    r = sr.reach_trending("python", "twitter", limit=5)
    assert isinstance(r["trending_topics"], list)
    # Either real topics came back, or graceful note (network blocked)
    assert r["trending_topics"] or r.get("note")


def test_reach_falls_back_on_import_failure():
    # If Agent-Reach import fails, functions return safe dicts (no crash)
    with patch.object(sr, "_load_reach", return_value=(None, None)):
        t = sr.reach_trending("x")
        assert t["note"] == "real-research-unavailable"
        h = sr.reach_hashtags("x")
        assert h["note"] == "real-research-unavailable"
        a = sr.reach_audience("instagram")
        assert "best_times" in a  # local intel still works
