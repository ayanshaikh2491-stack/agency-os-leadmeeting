# admin/tests/test_sba_lead_sources.py
import pytest

from admin.tools.sba_lead_sources import (
    NORMALIZED_FIELDS,
    SOURCES,
    dedupe_leads,
    find_leads,
    find_leads_all,
    normalize_lead,
)


class FakeChrome:
    """Records goto URLs and returns canned extract results."""

    def __init__(self):
        self.gotos = []

    async def goto(self, url, **kw):
        self.gotos.append(url)
        return {"ok": True}

    async def extract(self, selector=None, limit=20, **kw):
        return {
            "items": [
                {"text": "Al's Auto Repair", "href": "https://maps.example/p1"},
                {"text": "Dominguez Electric", "href": "https://maps.example/p2"},
            ]
        }

    async def read(self, **kw):
        return {"text": "Al's Auto Repair | (713) 555-0142 | 123 Main St, Houston, TX"}

    async def text(self, uid=None, **kw):
        return {"text": "Al's Auto Repair"}

    async def click(self, uid=None, selector=None, **kw):
        return {"ok": True}

    async def wait(self, what="load", pattern="", **kw):
        return {"ok": True}

    async def close(self, **kw):
        return {"ok": True}


def test_sources_registered():
    assert set(SOURCES) >= {"google_maps", "yelp", "yellowpages", "bing_maps", "facebook_pages"}


def test_normalize_lead_shape():
    card = {"name": "Bob's Plumbing", "address": "1 Main St", "phone": "555-0100",
            "city": "Houston", "state": "TX"}
    lead = normalize_lead(card, "yelp")
    for field in NORMALIZED_FIELDS:
        assert field in lead
    assert lead["source"] == "yelp"
    assert lead["verified"] is False


def test_dedupe_leads_merges_same_business():
    a = {"name": "Al's Auto", "phone": "555-0101", "sources": ["google_maps"], "verified": True}
    b = {"name": "Al's Auto", "phone": "555-0101", "sources": ["yelp"], "verified": True}
    out = dedupe_leads([a, b])
    assert len(out) == 1
    assert set(out[0]["sources"]) == {"google_maps", "yelp"}


@pytest.mark.asyncio
async def test_find_leads_google_maps_uses_chrome():
    chrome = FakeChrome()
    leads = await find_leads("google_maps", "plumber", "Houston", "TX", max_candidates=2, chrome=chrome)
    assert any("google.com/maps" in u for u in chrome.gotos)
    assert isinstance(leads, list)
    assert all(l["source"] == "google_maps" for l in leads)


@pytest.mark.asyncio
async def test_find_leads_all_collects_and_dedupes():
    chrome = FakeChrome()
    leads = await find_leads_all("plumber", "Houston", "TX", max_per_source=2, chrome=chrome)
    assert isinstance(leads, list)
    for lead in leads:
        assert set(lead["sources"])  # at least one source
        assert lead["verified"] is True or "verified" in lead
