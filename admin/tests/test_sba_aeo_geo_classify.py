"""SBA business classifier returns per-workspace AEO/GEO angles.

Proof: classify a plumbing / dental / law workspace and confirm the
specialized angle (used by every agent) is produced.
"""
import pytest

from admin.agency import sba_biztypes as b

# (workspace, industry, expected category, expected AEO angle fragment)
CASES = [
    ("Houston Plumbing Co", "plumbing", "plumbing", "emergency plumber near me"),
    ("Bright Smile Dental", "dentist clinic", "dentist", "best dentist for implants"),
    ("Metro Law Group", "law firm", "law", "best lawyer for divorce"),
]


@pytest.mark.parametrize("ws,ind,cat,expected_angle", CASES)
def test_classify_aeo_angle(ws, ind, cat, expected_angle):
    r = b.classify_business(ws, industry=ind)
    assert r["category"] == cat
    assert expected_angle in r["aeo_angle"]
    assert r["geo_angle"]  # non-empty GEO angle


def test_classify_unknown_returns_empty():
    # No business type detected -> no specialized angle (agents fall back to SEO).
    r = b.classify_business("My Cool Startup", industry="")
    assert r["category"] == ""
    assert r["aeo_angle"] == ""
    assert r["geo_angle"] == ""
