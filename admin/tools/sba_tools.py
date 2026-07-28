"""SBA Tools — Lead generation strategy + Chrome browser + lead store.

SBA (Sales/Business Agent) uses these tools to:
1. Analyse client market/industry and decide where to find leads
2. Browse platforms (Upwork, LinkedIn, Fiverr, web) via Chrome
3. Save, qualify, and manage leads

Follows the same pattern as seo_tools.py / ads_tools.py.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from admin.agency.sba_store import create_lead, list_leads

logger = logging.getLogger(__name__)

# ── Lead Source Strategy (industry + market → platform) ───────────────────


LEAD_SOURCE_MAP: dict[str, dict[str, list[str]]] = {
    # Most specific FIRST — Python dict preserves insertion order
    "b2b_saas": {
        "keywords": ["b2b", "saas", "enterprise", "b2b saas", "b2b software", "erp", "crm"],
        "platforms": ["linkedin", "crunchbase", "google"],
    },
    "tech_web": {
        "keywords": ["web development", "website", "web app", "full stack", "frontend", "backend", "react", "vue", "angular", "node", "django", "flask"],
        "platforms": ["upwork", "linkedin", "fiverr", "freelancer"],
    },
    "tech_mobile": {
        "keywords": ["mobile app", "ios", "android", "flutter", "react native"],
        "platforms": ["upwork", "linkedin", "fiverr"],
    },
    "marketing": {
        "keywords": ["marketing", "seo", "ads", "social media", "branding", "digital marketing", "ppc", "campaign", "growth hacking"],
        "platforms": ["linkedin", "upwork", "fiverr", "google"],
    },
    "consulting": {
        "keywords": ["consulting", "consultant", "strategy", "business", "coaching", "mentor"],
        "platforms": ["linkedin", "upwork"],
    },
    "software": {
        "keywords": ["software", "app", "developer", "programmer", "coding", "api", "python", "javascript", "java", "c++", "golang"],
        "platforms": ["upwork", "linkedin", "fiverr", "freelancer", "github"],
    },
    "design": {
        "keywords": ["design", "ui", "ux", "graphic design", "logo", "brand identity", "figma"],
        "platforms": ["upwork", "fiverr", "dribbble", "behance"],
    },
    "writing": {
        "keywords": ["writing", "copywriting", "content writing", "blog", "article", "ghostwriting", "writer", "copywriter"],
        "platforms": ["upwork", "fiverr", "linkedin", "medium"],
    },
    "video_photo": {
        "keywords": ["video", "photo", "editing", "animation", "motion", "photography", "videography"],
        "platforms": ["upwork", "fiverr", "linkedin"],
    },
    "ecommerce": {
        "keywords": ["ecommerce", "shopify", "woocommerce", "amazon", "dropshipping", "product"],
        "platforms": ["upwork", "linkedin", "google", "facebook"],
    },
    "local_business": {
        "keywords": ["local", "restaurant", "salon", "gym", "clinic", "plumber", "electrician", "mechanic", "dentist", "doctor"],
        "platforms": ["google maps", "yelp", "facebook", "instagram"],
    },
    "general": {
        "keywords": [],
        "platforms": ["upwork", "linkedin", "fiverr", "google"],
    },
}


def detect_lead_sources(industry: str, market: str = "global") -> dict[str, Any]:
    """Analyse client industry and market to recommend lead sources.

    Returns a dict with:
      - platforms: list of recommended platforms
      - why: reasoning for each platform
      - search_terms: suggested search terms for finding leads
    """
    ind_lower = industry.lower()
    matched = LEAD_SOURCE_MAP.get("general")
    matched_key = "general"

    for key, config in LEAD_SOURCE_MAP.items():
        for kw in config["keywords"]:
            if kw in ind_lower:
                matched = config
                matched_key = key
                break
        if matched_key != "general":
            break

    platforms = list(matched["platforms"])

    # Market-specific adjustments
    market_lower = market.lower()
    if market_lower in ("india", "in"):
        if "upwork" not in platforms:
            platforms.append("upwork")
        platforms.append("freelancer")
    elif market_lower in ("uae", "dubai", "middle east", "saudi"):
        platforms.append("upwork")
        platforms.append("linkedin")
    elif market_lower in ("uk", "us", "usa", "canada", "australia", "europe"):
        platforms.append("linkedin")
        platforms.append("upwork")

    # Remove duplicates while preserving order
    seen: set[str] = set()
    unique_platforms: list[str] = []
    for p in platforms:
        if p.lower() not in seen:
            seen.add(p.lower())
            unique_platforms.append(p)

    # Why each platform
    why_map: dict[str, str] = {
        "upwork": "Freelance job posts — search relevant skills, submit proposals",
        "linkedin": "Professional network — search people, companies, post content",
        "fiverr": "Service marketplace — find buyers looking for specific services",
        "freelancer": "Freelance platform — alternative to Upwork with project bids",
        "google maps": "Local business directory — find businesses by category + location",
        "yelp": "Local reviews — find businesses with specific needs",
        "dribbble": "Design portfolio platform — find companies hiring designers",
        "behance": "Creative portfolio platform — similar to Dribbble",
        "crunchbase": "Company database — find funded startups and decision makers",
        "google": "Web search — targeted search queries for lead discovery",
        "facebook": "Social platform — local business groups, marketplace",
        "instagram": "Visual platform — engage with potential clients in niche",
        "medium": "Content platform — find writers and businesses publishing",
    }

    search_terms = []
    if industry:
        for p in unique_platforms:
            search_terms.append(f"{industry} {p}")

    return {
        "industry": industry,
        "market": market,
        "matched_category": matched_key,
        "platforms": unique_platforms,
        "why": {p: why_map.get(p, f"Search {p} for leads") for p in unique_platforms},
        "search_terms": search_terms[:5],
    }


def save_lead_record(
    name: str = "",
    business_name: str = "",
    email: str = "",
    phone: str = "",
    source: str = "manual",
    score: int = 50,
    notes: str = "",
) -> dict[str, Any]:
    """Save a lead to the lead store.

    Returns the created lead record.
    """
    notes_list = []
    if notes:
        notes_list.append({"text": notes, "timestamp": __import__("datetime").datetime.now().isoformat()})

    # Run async create_lead synchronously
    try:
        import asyncio
        loop = asyncio.get_event_loop()
        lead = asyncio.run_coroutine_threadsafe(
            create_lead({
                "name": name,
                "business_name": business_name,
                "email": email,
                "phone": phone,
                "source": source,
                "score": score,
                "notes": notes_list,
            }),
            loop,
        ).result(timeout=10)
        return {"status": "ok", "lead_id": lead.get("id", ""), "lead": {k: v for k, v in lead.items() if k in ("id", "name", "business_name", "source", "score", "status")}}
    except RuntimeError:
        # No event loop running — create a new one
        import asyncio
        try:
            lead = asyncio.run(
                create_lead({
                    "name": name,
                    "business_name": business_name,
                    "email": email,
                    "phone": phone,
                    "source": source,
                    "score": score,
                    "notes": notes_list,
                })
            )
            return {"status": "ok", "lead_id": lead.get("id", ""), "lead": {k: v for k, v in lead.items() if k in ("id", "name", "business_name", "source", "score", "status")}}
        except Exception as e2:
            return {"status": "error", "error": str(e2)}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def list_saved_leads(status: str | None = None) -> list[dict[str, Any]]:
    """List all saved leads, optionally filtered by status."""
    return list_leads(status=status)


def qualify_lead(
    lead_score: int,
    has_budget: bool = False,
    has_authority: bool = False,
    has_need: bool = False,
    has_timeline: bool = False,
    notes: str = "",
) -> dict[str, Any]:
    """Qualify a lead using BANT framework.

    Returns qualification result with score and recommendation.
    """
    criteria_met = sum([has_budget, has_authority, has_need, has_timeline])
    total = 4
    pct = (criteria_met / total) * 100 if total else 0

    combined_score = (lead_score * 0.4 + pct * 0.6)
    combined_score = min(100, max(0, combined_score))

    if combined_score >= 80:
        verdict = "hot"
        recommendation = "Ready for CEO handoff — schedule meeting"
    elif combined_score >= 50:
        verdict = "warm"
        recommendation = "Needs nurturing — follow up with value content"
    else:
        verdict = "cold"
        recommendation = "Low priority — keep in pipeline, revisit later"

    return {
        "lead_score": lead_score,
        "bant": {
            "budget": has_budget,
            "authority": has_authority,
            "need": has_need,
            "timeline": has_timeline,
            "criteria_met": criteria_met,
        },
        "combined_score": round(combined_score, 1),
        "verdict": verdict,
        "recommendation": recommendation,
    }


# ── OpenAI function-calling tool definitions ──────────────────────────────

SBA_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "detect_lead_sources",
            "description": "Analyse client industry and market to recommend the BEST platforms for finding leads. Use this FIRST when starting lead gen for a new client.",
            "parameters": {
                "type": "object",
                "properties": {
                    "industry": {"type": "string", "description": "Client's industry (e.g. 'web development', 'marketing', 'ecommerce')"},
                    "market": {"type": "string", "description": "Target market (e.g. 'global', 'us', 'india', 'uae', 'uk')"},
                },
                "required": ["industry", "market"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_lead_record",
            "description": "Save a qualified lead to the workspace lead store. Call this when you find a promising lead through Chrome browsing.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Lead name or contact person"},
                    "business_name": {"type": "string", "description": "Company/business name"},
                    "email": {"type": "string", "description": "Email address if found"},
                    "phone": {"type": "string", "description": "Phone number if found"},
                    "source": {"type": "string", "description": "Where you found this lead (e.g. 'upwork', 'linkedin', 'fiverr')"},
                    "score": {"type": "integer", "description": "Lead quality score 0-100"},
                    "notes": {"type": "string", "description": "Key details about the lead"},
                },
                "required": ["name", "business_name", "source"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_saved_leads",
            "description": "List all leads saved in the store, optionally filtered by status (new/contacted/meeting/proposal/closed/lost).",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "Filter by status: new, contacted, meeting, proposal, closed, lost"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "qualify_lead",
            "description": "Qualify a lead using BANT framework (Budget, Authority, Need, Timeline). Returns a score and recommendation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lead_score": {"type": "integer", "description": "Your gut feeling score 0-100"},
                    "has_budget": {"type": "boolean", "description": "Does the lead have budget?"},
                    "has_authority": {"type": "boolean", "description": "Does the lead have decision-making authority?"},
                    "has_need": {"type": "boolean", "description": "Does the lead have a clear need?"},
                    "has_timeline": {"type": "boolean", "description": "Does the lead have a timeline?"},
                    "notes": {"type": "string", "description": "Additional context"},
                },
                "required": ["lead_score"],
            },
        },
    },
]


# ── Dispatch ──────────────────

SBA_TOOL_DISPATCH: dict[str, str] = {
    "detect_lead_sources": "detect_lead_sources",
    "save_lead_record": "save_lead_record",
    "list_saved_leads": "list_saved_leads",
    "qualify_lead": "qualify_lead",
}


def execute_sba_tool(tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Execute an SBA tool by name and return the result."""
    dispatch = {
        "detect_lead_sources": lambda: detect_lead_sources(
            args.get("industry", ""), args.get("market", "global"),
        ),
        "save_lead_record": lambda: save_lead_record(
            name=args.get("name", ""),
            business_name=args.get("business_name", ""),
            email=args.get("email", ""),
            phone=args.get("phone", ""),
            source=args.get("source", "manual"),
            score=args.get("score", 50),
            notes=args.get("notes", ""),
        ),
        "list_saved_leads": lambda: list_saved_leads(status=args.get("status")),
        "qualify_lead": lambda: qualify_lead(
            lead_score=args.get("lead_score", 50),
            has_budget=args.get("has_budget", False),
            has_authority=args.get("has_authority", False),
            has_need=args.get("has_need", False),
            has_timeline=args.get("has_timeline", False),
            notes=args.get("notes", ""),
        ),
    }

    fn = dispatch.get(tool_name)
    if not fn:
        return {"error": f"Unknown SBA tool: {tool_name}"}

    try:
        result = fn()
        return result
    except Exception as e:
        logger.exception("SBA tool %s failed", tool_name)
        return {"error": f"{tool_name} failed: {str(e)[:200]}"}
