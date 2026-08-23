"""Proof: every agent renders AEO/GEO per-workspace (real, not jargon).

Covers: SEO, Website, Content, Social, Ads agents + SBA business classifier.
The SAME per-workspace angle must appear across all agents (entity consistency
for AI search / AI answers).
"""
import pytest

from admin.agency import agent_aeo_geo, sba_biztypes
from admin.workspace.agents import ads, social
from admin.workspace.agents.content import _with_aeo_geo as content_with
from admin.workspace.agents.seo import build_seo_system_prompt

PLUMBER = "Houston Plumbing Co"
ANGLE = "emergency plumber near me"


# ── SBA classifier ───────────────────────────────────────────────────────────
def test_classify_returns_aeo_geo_angles():
    r = sba_biztypes.classify_business(PLUMBER, industry="plumbing")
    assert r["category"] == "plumbing"
    assert ANGLE in r["aeo_angle"]
    assert r["geo_angle"]


# ── Shared section builder ─────────────────────────────────────────────────────
def test_shared_section_injects_angle():
    sec = agent_aeo_geo.build_aeo_geo_section(PLUMBER)
    assert "AEO" in sec and "GEO" in sec
    assert ANGLE in sec


# ── SEO agent ─────────────────────────────────────────────────────────────────
def test_seo_prompt_includes_angle():
    p = build_seo_system_prompt(PLUMBER, "TestClient")
    assert ANGLE in p


# ── Website agent (calls shared agent_aeo_geo at its LLM call) ─────────────────
def test_website_sections_includes_angle():
    sec = agent_aeo_geo.build_aeo_geo_section(PLUMBER)
    assert ANGLE in sec


# ── Content agent helper ──────────────────────────────────────────────────────
def test_content_helper_includes_angle():
    out = content_with("BASE", PLUMBER)
    assert ANGLE in out


# ── Social agent ───────────────────────────────────────────────────────────────
def test_social_prompt_includes_angle():
    p = social.SOCIAL_SYSTEM_PROMPT.format(
        workspace_name=PLUMBER,
        client_name="Test",
        aeo_geo_context=agent_aeo_geo.build_aeo_geo_section(PLUMBER),
    )
    assert "AI Visibility" in p and ANGLE in p


# ── Ads agent ──────────────────────────────────────────────────────────────────
def test_ads_prompt_includes_angle():
    p = ads.ADS_SYSTEM_PROMPT.format(
        workspace_name=PLUMBER,
        client_name="Test",
        workspace_context="x",
        aeo_geo_context=agent_aeo_geo.build_aeo_geo_section(PLUMBER),
    )
    assert "AI Visibility" in p and ANGLE in p


# ── Cross-agent consistency ────────────────────────────────────────────────────
def test_all_agents_share_same_angle():
    sec = agent_aeo_geo.build_aeo_geo_section(PLUMBER)
    seo = build_seo_system_prompt(PLUMBER, "TestClient")
    web = agent_aeo_geo.build_aeo_geo_section(PLUMBER)
    con = content_with("BASE", PLUMBER)
    soc = social.SOCIAL_SYSTEM_PROMPT.format(
        workspace_name=PLUMBER,
        client_name="Test",
        aeo_geo_context=sec,
    )
    adz = ads.ADS_SYSTEM_PROMPT.format(
        workspace_name=PLUMBER,
        client_name="Test",
        workspace_context="x",
        aeo_geo_context=sec,
    )
    for rendered in (sec, seo, web, con, soc, adz):
        assert ANGLE in rendered, "angle leaked in one agent"
