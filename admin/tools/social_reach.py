"""Social Reach — real research data for the Social Media Agent.

Wraps the FREE, zero-config channels of Agent-Reach (Web via Jina Reader,
V2EX public API) so the social agent's trend / competitor / hashtag /
audience tools return REAL data instead of LLM-only scaffolding.

Design rules (per user):
- ONLY the Social Media Agent uses this. No other agent touches it.
- Lightweight, ₹0, no Chrome, no login. Only Web + V2EX (free tiers).
- Safe: if Agent-Reach import fails or network errors, fall back to a
  structured "unavailable" dict so the agent never crashes.

Usage:
    from admin.tools.social_reach import (
        reach_trending, reach_competitor, reach_hashtags, reach_audience
    )
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


# ── Lazy Agent-Reach loader (keeps import cheap + safe) ─────────────────────
def _load_reach():
    """Return (WebChannel, V2EXChannel) or (None, None) if unavailable."""
    try:
        # Agent-Reach uses root-style imports internally (from agent_reach...).
        # Register our bundled copy under that name so those imports resolve.
        import admin.tools.agent_reach as _pkg
        import sys as _sys
        _sys.modules.setdefault("agent_reach", _pkg)
        from admin.tools.agent_reach.channels.web import WebChannel
        from admin.tools.agent_reach.channels.v2ex import V2EXChannel
        return WebChannel(), V2EXChannel()
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Agent-Reach unavailable: %s", exc)
        return None, None


# ── Real trending topics ─────────────────────────────────────────────────────
def reach_trending(topic: str = "", platform: str = "instagram", limit: int = 10) -> dict[str, Any]:
    """Real trending discussion + formats for a topic (Web + V2EX)."""
    web, v2ex = _load_reach()
    result: dict[str, Any] = {
        "topic": topic,
        "platform": platform,
        "source": "agent-reach",
        "trending_topics": [],
        "trending_formats": ["Reels", "Carousel", "Stories", "Live"],
        "note": "",
    }
    if v2ex is None and web is None:
        result["note"] = "real-research-unavailable"
        return result

    # V2EX hot topics = real current discussions
    if v2ex is not None:
        try:
            for t in v2ex.get_hot_topics(limit=limit):
                result["trending_topics"].append({
                    "title": t.get("title", ""),
                    "replies": t.get("replies", 0),
                    "node": t.get("node_title", ""),
                    "url": t.get("url", ""),
                })
        except Exception as exc:
            logger.warning("V2EX trend fetch failed: %s", exc)
            result["note"] = f"v2ex-unavailable: {exc}"

    # Web: read a trending/explore page for the topic when given
    if web is not None and topic:
        try:
            page = web.read(f"https://www.google.com/search?q={topic}+trending")
            # crude signal: pull first ~1500 chars of real page text
            snippet = page[:1500].strip()
            if snippet:
                result["trending_topics"].append({
                    "title": f"web:{topic}",
                    "source": "web",
                    "snippet": snippet,
                })
        except Exception as exc:
            logger.warning("Web trend fetch failed: %s", exc)

    if not result["trending_topics"]:
        result["note"] = "no-real-data-returned"
    return result


# ── Real competitor analysis ─────────────────────────────────────────────────
def reach_competitor(competitor: str = "", platform: str = "instagram") -> dict[str, Any]:
    """Real public info about a competitor (Web read of their page)."""
    web, _ = _load_reach()
    result: dict[str, Any] = {
        "competitor": competitor,
        "platform": platform,
        "source": "agent-reach",
        "profile": {},
        "posts_sample": [],
        "note": "",
    }
    if web is None or not competitor:
        result["note"] = "real-research-unavailable"
        return result
    # Try to read a public profile / page for the competitor
    handle = competitor.lstrip("@").replace(" ", "")
    urls = [
        f"https://www.instagram.com/{handle}/",
        f"https://www.linkedin.com/company/{handle}/",
        f"https://twitter.com/{handle}",
    ]
    for u in urls:
        try:
            text = web.read(u)
            result["profile"][u] = text[:1200].strip()
        except Exception as exc:
            logger.warning("Competitor fetch %s failed: %s", u, exc)
    if not result["profile"]:
        result["note"] = "profile-unreachable-read-only"
    return result


# ── Real hashtag research ────────────────────────────────────────────────────
def reach_hashtags(topic: str = "", platform: str = "instagram", count: int = 20) -> dict[str, Any]:
    """Real hashtag context for a topic (Web + V2EX node topics)."""
    web, v2ex = _load_reach()
    result: dict[str, Any] = {
        "topic": topic,
        "platform": platform,
        "requested_count": count,
        "categories": {
            "high_reach": "Hashtags with 1M+ posts (for visibility)",
            "medium_reach": "Hashtags with 100k-1M posts (for balance)",
            "niche": "Hashtags with 10k-100k posts (for targeting)",
            "branded": "Brand-specific hashtags",
        },
        "suggested": [],
        "note": "",
    }
    if web is None and v2ex is None:
        result["note"] = "real-research-unavailable"
        return result

    # V2EX node topics for the topic = real discussion themes -> hashtag seeds
    if v2ex is not None and topic:
        try:
            for t in v2ex.get_node_topics(topic, limit=8):
                result["suggested"].append(f"#{t.get('node_name','')} {t.get('title','')[:40]}")
        except Exception as exc:
            logger.warning("V2EX hashtag fetch failed: %s", exc)

    # Web: search the topic + hashtag to find real usage
    if web is not None and topic:
        try:
            page = web.read(f"https://www.google.com/search?q=%23{topic}")
            if page:
                result["suggested"].append(f"web-snippet:{page[:300].strip()}")
        except Exception as exc:
            logger.warning("Web hashtag fetch failed: %s", exc)

    if not result["suggested"]:
        result["note"] = "no-real-hashtags-returned"
    return result


# ── Real audience analysis ────────────────────────────────────────────────────
def reach_audience(platform: str = "instagram", industry: str = "") -> dict[str, Any]:
    """Audience dimensions for a platform + industry (real platform intel)."""
    web, _ = _load_reach()
    # Platform demographics come from the social agent's own intel (real, local).
    try:
        from admin.tools.social_tools import get_platform_intelligence
        intel = get_platform_intelligence(platform)
    except Exception:
        intel = {}
    result: dict[str, Any] = {
        "platform": platform,
        "industry": industry,
        "analysis_dimensions": ["demographics", "psychographics", "behavior", "preferences"],
        "algorithm_factors": intel.get("algorithm_factors", []),
        "best_times": intel.get("best_times", {}),
        "best_practices": intel.get("best_practices", []),
        "source": "local-intel",
        "note": "",
    }
    if web is not None and industry:
        try:
            page = web.read(f"https://www.google.com/search?q={industry}+audience+demographics+{platform}")
            if page:
                result["web_signal"] = page[:500].strip()
        except Exception as exc:
            logger.warning("Web audience fetch failed: %s", exc)
    return result
