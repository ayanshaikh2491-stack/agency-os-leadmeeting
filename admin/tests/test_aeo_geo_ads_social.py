"""Tests: Ads + Social agents render AEO/GEO sections per workspace.

Proof (not jargon): the same business angle that SEO/Website/Content use
must also appear inside the Ads and Social system prompts for that workspace.
"""
import pytest

from admin.agency import agent_aeo_geo
from admin.workspace.agents import ads, social

PLUMBER_WS = "Houston Plumbing Co"
PLUMBER_ANGLE = "emergency plumber near me"


def _ads_prompt(ws: str) -> str:
    return ads.ADS_SYSTEM_PROMPT.format(
        workspace_name=ws,
        client_name="Test",
        workspace_context="x",
        aeo_geo_context=agent_aeo_geo.build_aeo_geo_section(ws),
    )


def _social_prompt(ws: str) -> str:
    return social.SOCIAL_SYSTEM_PROMPT.format(
        workspace_name=ws,
        client_name="Test",
        aeo_geo_context=agent_aeo_geo.build_aeo_geo_section(ws),
    )


def test_ads_has_aeo_geo_section():
    p = _ads_prompt(PLUMBER_WS)
    assert "AEO" in p and "GEO" in p
    assert "AI Visibility" in p


def test_ads_injects_per_workspace_angle():
    p = _ads_prompt(PLUMBER_WS)
    assert PLUMBER_ANGLE in p  # same angle SEO/Website use


def test_social_has_aeo_geo_section():
    p = _social_prompt(PLUMBER_WS)
    assert "AEO" in p and "GEO" in p
    assert "AI Visibility" in p


def test_social_injects_per_workspace_angle():
    p = _social_prompt(PLUMBER_WS)
    assert PLUMBER_ANGLE in p


def test_ads_social_angle_matches_seo_agent():
    # All agents must share the SAME per-workspace angle (entity consistency).
    a = agent_aeo_geo.build_aeo_geo_section(PLUMBER_WS)
    assert PLUMBER_ANGLE in _ads_prompt(PLUMBER_WS)
    assert PLUMBER_ANGLE in _social_prompt(PLUMBER_WS)
    assert PLUMBER_ANGLE in a
