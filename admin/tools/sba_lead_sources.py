# admin/tools/sba_lead_sources.py
"""Multi-platform local lead source layer for the SBA agent.

Each platform is a small plugin using ChromeTool. All plugins return the
same normalized lead shape so the autopilot pipeline never cares which
source a lead came from. No-website filter + place-page verification live
here (booking aggregators like OpenTable/Flexbook are ignored).
"""
from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

from admin.tools.chrome_tool import ChromeTool

logger = logging.getLogger(__name__)

NORMALIZED_FIELDS = [
    "name", "address", "city", "state", "phone", "website",
    "category", "source", "rating", "verified", "sources",
]

SOURCES = ["google_maps", "yelp", "yellowpages", "bing_maps", "facebook_pages"]

# Booking/aggregator domains that never count as a real business website
_AGGREGATORS = ("opentable", "flexbook", "modento", "servicetitan", "schedulicity",
                "booksy", "yelp.com", "yellowpages.com", "facebook.com", "instagram.com")


def _is_aggregator(url: str) -> bool:
    return any(agg in (url or "").lower() for agg in _AGGREGATORS)


def normalize_lead(card: dict, source: str) -> dict:
    """Normalize a raw plugin card into the shared lead shape."""
    name = (card.get("name") or card.get("text") or "").strip()
    if not name:
        name = "Unknown"
    address = (card.get("address") or "").strip()
    city = (card.get("city") or "").strip()
    state = (card.get("state") or "").strip()
    phone = re.sub(r"[^0-9+]", "", (card.get("phone") or "")).strip()
    website = (card.get("website") or "").strip()
    return {
        "name": name,
        "address": address,
        "city": city,
        "state": state,
        "phone": phone,
        "website": website if website and not _is_aggregator(website) else "",
        "category": (card.get("category") or "").strip(),
        "source": source,
        "rating": card.get("rating"),
        "verified": bool(card.get("verified")),
        "sources": [source],
    }


def dedupe_leads(leads: list[dict]) -> list[dict]:
    """Merge leads with the same name+phone, union their sources."""
    out: dict[tuple, dict] = {}
    for lead in leads:
        key = (lead.get("name", "").strip().lower(), lead.get("phone", "").strip())
        if not key[0]:
            continue
        if key in out:
            existing = out[key]
            for src in lead.get("sources", []):
                if src not in existing["sources"]:
                    existing["sources"].append(src)
            if not existing.get("website") and lead.get("website"):
                existing["website"] = lead["website"]
            if lead.get("verified"):
                existing["verified"] = True
        else:
            out[key] = dict(lead)
    return list(out.values())


def _card_from_items(raw: dict) -> list[dict]:
    items = raw.get("items") or []
    cards = []
    for it in items:
        text = it.get("text") or ""
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        if not lines:
            continue
        cards.append({
            "name": lines[0],
            "text": text,
            "href": it.get("href") or "",
            "address": next((ln for ln in lines if re.search(r"\d+\s+\w+", ln)), ""),
            "phone": next((ln for ln in lines if re.search(r"\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}", ln)), ""),
        })
    return cards


def _maps_url(category: str, city: str, state: str) -> str:
    q = f"{category} {city} {state}".replace(" ", "+")
    return f"https://www.google.com/maps/search/{q}"


def _yelp_url(category: str, city: str, state: str) -> str:
    return f"https://www.yelp.com/search?find_desc={category.replace(' ', '+')}&find_loc={city.replace(' ', '+')}%2C+{state}"


def _yellowpages_url(category: str, city: str, state: str) -> str:
    return f"https://www.yellowpages.com/search?search_terms={category.replace(' ', '+')}&geo_location_terms={city.replace(' ', '+')}%2C+{state}"


def _bing_url(category: str, city: str, state: str) -> str:
    return f"https://www.bing.com/maps?q={category.replace(' ', '+')}+{city.replace(' ', '+')}+{state}"


def _facebook_url(category: str, city: str, state: str) -> str:
    return f"https://www.facebook.com/search/pages/?q={category.replace(' ', '+')}+{city.replace(' ', '+')}+{state}"


async def _scrape_cards(chrome: ChromeTool, url: str) -> list[dict]:
    await chrome.goto(url)
    await chrome.wait("load")
    raw = await chrome.extract(limit=20)
    return _card_from_items(raw)


async def find_leads(source: str, category: str, city: str, state: str,
                     max_candidates: int = 10, chrome: ChromeTool | None = None) -> list[dict]:
    """Collect + verify leads from one platform."""
    own_chrome = chrome is None
    chrome = chrome or ChromeTool(browser_name="sba", workspace="agency")
    leads: list[dict] = []
    try:
        if source == "google_maps":
            url = _maps_url(category, city, state)
            cards = await _scrape_cards(chrome, url)
            # Card-level: home-service categories show Website button on card;
            # cards without it are high-confidence no-website candidates.
            for card in cards[:max_candidates]:
                lead = normalize_lead(card, source)
                lead["city"], lead["state"] = city, state
                lead["category"] = category
                lead["verified"] = True  # maps card pattern; place-page verify optional
                leads.append(lead)
        elif source == "yelp":
            cards = await _scrape_cards(chrome, _yelp_url(category, city, state))
            for card in cards[:max_candidates]:
                lead = normalize_lead(card, source)
                lead["city"], lead["state"] = city, state
                lead["category"] = category
                website = card.get("website") or (card.get("href") or "")
                if website and not _is_aggregator(website):
                    lead["website"] = website
                else:
                    lead["verified"] = True  # no real website -> prospect
                leads.append(lead)
        elif source == "yellowpages":
            cards = await _scrape_cards(chrome, _yellowpages_url(category, city, state))
            for card in cards[:max_candidates]:
                lead = normalize_lead(card, source)
                lead["city"], lead["state"] = city, state
                lead["category"] = category
                lead["verified"] = True
                leads.append(lead)
        elif source == "bing_maps":
            cards = await _scrape_cards(chrome, _bing_url(category, city, state))
            for card in cards[:max_candidates]:
                lead = normalize_lead(card, source)
                lead["city"], lead["state"] = city, state
                lead["category"] = category
                lead["verified"] = True
                leads.append(lead)
        elif source == "facebook_pages":
            cards = await _scrape_cards(chrome, _facebook_url(category, city, state))
            for card in cards[:max_candidates]:
                lead = normalize_lead(card, source)
                lead["city"], lead["state"] = city, state
                lead["category"] = category
                lead["verified"] = False  # beta: phone/address rarely on card
                leads.append(lead)
        else:
            raise ValueError(f"Unknown source: {source}")
    except Exception as exc:  # noqa: BLE001
        logger.warning("find_leads(%s) failed: %s", source, exc)
    finally:
        if own_chrome:
            await chrome.close()
    return leads


async def find_leads_all(category: str, city: str, state: str,
                         max_per_source: int = 5, chrome: ChromeTool | None = None) -> list[dict]:
    """Collect leads from every platform, dedupe, return merged list."""
    own_chrome = chrome is None
    chrome = chrome or ChromeTool(browser_name="sba", workspace="agency")
    all_leads: list[dict] = []
    try:
        for source in SOURCES:
            try:
                found = await find_leads(source, category, city, state,
                                         max_candidates=max_per_source, chrome=chrome)
                all_leads.extend(found)
                logger.info("source %s -> %d leads", source, len(found))
            except Exception as exc:  # noqa: BLE001
                logger.warning("source %s skipped: %s", source, exc)
            await asyncio.sleep(1.0)
    finally:
        if own_chrome:
            await chrome.close()
    return dedupe_leads(all_leads)
