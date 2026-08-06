# admin/tests/test_social_skills.py
from admin.agency.social_skills import SOCIAL_SKILL_REGISTRY, detect_skills, build_skill_context, list_social_skills


def test_registry_has_social_skills():
    names = [s["name"] for s in SOCIAL_SKILL_REGISTRY]
    assert "ad-creative" in names
    assert "social" in names
    assert "content-engine" in names


def test_detect_skills_finds_ad_creative():
    hits = detect_skills("make me ad copy variations for facebook ads", max_skills=2)
    names = [h["name"] for h in hits]
    assert "ad-creative" in names


def test_detect_skills_finds_social():
    hits = detect_skills("what should I post on linkedin this week")
    names = [h["name"] for h in hits]
    assert "social" in names


def test_build_skill_context_returns_string():
    ctx = build_skill_context([{"name": "social", "description": "d"}])
    assert isinstance(ctx, str)
    assert "social" in ctx


def test_list_social_skills():
    assert len(list_social_skills()) >= 3
