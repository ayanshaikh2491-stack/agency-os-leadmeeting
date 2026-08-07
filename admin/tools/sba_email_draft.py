# admin/tools/sba_email_draft.py
"""Professional cold outreach email drafting for the SBA autopilot.

Uses the SBA skill registry (cold-email, alex-hormozi-pitch, etc.) to build
context, then the configured LLM (WORKSPACE_*) drafts a personalized email.
Falls back to a clean template if the LLM is unavailable or fails.
"""
from __future__ import annotations

import logging
from typing import Any

from admin.config import settings

logger = logging.getLogger(__name__)


def fallback_email(lead: dict) -> tuple[str, str]:
    name = lead.get("name") or "there"
    category = lead.get("category") or "local business"
    subject = f"Quick question for {name}"
    body = (
        f"Hi {name},\n\n"
        f"I came across {name} and noticed you're a {category} in the local area. "
        "We're TAGS Agency, and we help local businesses get more customers with "
        "a professional website and local SEO.\n\n"
        "Would you be open to a quick 15-minute call this week to see if we can help?\n\n"
        "Best,\nAyan\nTAGS Agency"
    )
    return subject, body


async def _llm_draft(lead: dict, skill_context: str, angle: str | None = None) -> tuple[str, str]:
    """Call the configured LLM to draft a personalized email."""
    import openai

    client = openai.AsyncOpenAI(
        api_key=settings.WORKSPACE_API_KEY or None,
        base_url=settings.WORKSPACE_API_BASE or None,
    )
    name = lead.get("name") or "the business"
    category = lead.get("category") or "local business"
    city_state = f"{lead.get('city')}, {lead.get('state')}".strip(" ,")
    system = (
        "You are a sharp cold-outreach copywriter for TAGS Agency, a web design + "
        "local SEO agency. Write ONE professional, personalized cold email to a "
        "local business. Keep it short (under 120 words), friendly, specific, "
        "and end with a soft CTA for a 15-minute call.\n\n"
        f"RELEVANT SKILLS:\n{skill_context}"
    )
    if angle:
        # Layer 3: the agent's current strategy angle, decided by its own review.
        system += f"\n\nCURRENT MESSAGE ANGLE (weave this in naturally, do not quote it):\n{angle}"
    user = (
        f"Lead: {name} ({category}) in {city_state}. "
        "Return JSON: {\"subject\": \"...\", \"body\": \"...\"}. Body plain text only."
    )
    resp = await client.chat.completions.create(
        model=settings.WORKSPACE_AGENT_MODEL,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.5,
    )
    content = (resp.choices[0].message.content or "").strip()
    import json
    import re

    m = re.search(r"\{.*\}", content, re.DOTALL)
    if not m:
        raise ValueError("LLM did not return JSON")
    data = json.loads(m.group(0))
    subject = data.get("subject") or f"Quick question for {name}"
    body = data.get("body") or fallback_email(lead)[1]
    return subject, body


async def draft_email(lead: dict, angle: str | None = None) -> tuple[str, str]:
    """Draft a professional email; fall back to template on any failure."""
    try:
        from admin.agency.sba_skills import build_skill_context, detect_skills

        skills = detect_skills(f"cold outreach email to {lead.get('name', '')}", max_skills=2)
        ctx = build_skill_context(skills) if skills else "No extra skills matched."
        return await _llm_draft(lead, ctx, angle=angle)
    except Exception as exc:  # noqa: BLE001
        logger.warning("LLM email draft failed (%s); using template", exc)
        return fallback_email(lead)
