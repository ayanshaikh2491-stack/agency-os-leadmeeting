"""Structured Brief Builder — Domain Agents ke liye shared brief format.

Har domain agent isi format mein brief bhejta hai Content Agent ko.
Reasoning Chain ko sab information mil jaati hai.
"""
from __future__ import annotations

from typing import Any


def build_domain_brief(
    domain: str,
    content_type: str,
    topic: str,
    platform: str = "instagram",
    description: str = "",
    style: str = "bold",
    priority: str = "normal",
    quantity: int = 1,
    # Domain-specific fields
    objective: str = "engagement",
    target_audience: dict[str, Any] | None = None,
    emotional_hook: str = "curiosity",
    cta: str = "learn_more",
    key_message: str = "",
    competitor_context: str = "",
    constraints: str = "",
    copy_text: str = "",
    brand_guidelines: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Structured brief banao jo Content Agent ko samajh aaye.

    Args:
        domain: "ads", "social", "seo", "website"
        content_type: "ad_creative", "social_post", "hero_image", etc.
        topic: Brief topic/subject
        platform: Where it will be published
        description: Detailed description
        style: "bold", "minimal", "professional", etc.
        priority: "normal", "high", "urgent"
        quantity: Number of variations needed
        objective: "lead_generation", "brand_awareness", "engagement", "conversions"
        target_audience: {"age": "...", "interests": [...], "pain_points": [...]}
        emotional_hook: "fear", "curiosity", "trust", "excitement", "urgency", "FOMO"
        cta: "sign_up", "buy_now", "learn_more", "contact_us"
        key_message: The ONE thing this visual must communicate
        competitor_context: What competitors are doing
        constraints: Any limitations
        copy_text: Text that will appear on the visual
        brand_guidelines: Brand-specific guidelines
    """
    brief = {
        "domain": domain,
        "content_type": content_type,
        "topic": topic,
        "platform": platform,
        "description": description,
        "style": style,
        "priority": priority,
        "quantity": quantity,
        "objective": objective,
        "target_audience": target_audience or {
            "age": "25-45",
            "interests": [],
            "pain_points": [],
        },
        "emotional_hook": emotional_hook,
        "cta": cta,
        "key_message": key_message or topic,
        "competitor_context": competitor_context,
        "constraints": constraints,
        "copy_text": copy_text,
        "brand_guidelines": brand_guidelines or {},
    }

    # Domain-specific enhancements
    if domain == "ads":
        brief["objective"] = objective or "lead_generation"
        brief["conversion_focus"] = True
    elif domain == "social":
        brief["objective"] = objective or "engagement"
        brief["engagement_focus"] = True
    elif domain == "seo":
        brief["objective"] = objective or "traffic"
        brief["traffic_focus"] = True
    elif domain == "website":
        brief["objective"] = objective or "trust"
        brief["trust_focus"] = True

    return brief


def brief_to_text(brief: dict[str, Any]) -> str:
    """Structured brief ko human-readable text mein convert karo.
    
    Yeh text Content Agent ko seedha milta hai.
    """
    lines = [
        f"=== {brief['domain'].upper()} CONTENT REQUEST ===",
        f"",
        f"Content Type: {brief['content_type']}",
        f"Topic: {brief['topic']}",
        f"Platform: {brief['platform']}",
        f"Style: {brief['style']}",
        f"Priority: {brief['priority']}",
        f"Quantity: {brief['quantity']}",
        f"",
        f"--- STRATEGY ---",
        f"Objective: {brief['objective']}",
        f"Emotional Hook: {brief['emotional_hook']}",
        f"CTA: {brief['cta']}",
        f"Key Message: {brief['key_message']}",
    ]

    # Target audience
    audience = brief.get("target_audience", {})
    if audience:
        lines.append(f"")
        lines.append(f"--- TARGET AUDIENCE ---")
        lines.append(f"Age: {audience.get('age', '25-45')}")
        if audience.get("interests"):
            lines.append(f"Interests: {', '.join(audience['interests'])}")
        if audience.get("pain_points"):
            lines.append(f"Pain Points: {', '.join(audience['pain_points'])}")

    # Additional context
    if brief.get("description"):
        lines.append(f"")
        lines.append(f"--- DESCRIPTION ---")
        lines.append(brief["description"])

    if brief.get("copy_text"):
        lines.append(f"")
        lines.append(f"--- COPY TEXT ---")
        lines.append(brief["copy_text"])

    if brief.get("competitor_context"):
        lines.append(f"")
        lines.append(f"--- COMPETITOR CONTEXT ---")
        lines.append(brief["competitor_context"])

    if brief.get("constraints"):
        lines.append(f"")
        lines.append(f"--- CONSTRAINTS ---")
        lines.append(brief["constraints"])

    return "\n".join(lines)
