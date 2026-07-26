"""Content Agent — Workspace-Aware Visual Content Executor (6-Node Pipeline).

LANGGRAPH PIPELINE (6 nodes):
  Node 1: parse_brief     — Extract structured brief from raw message
  Node 2: analyze_brand   — Combine brand context + agency knowledge
  Node 3: plan_visual     — Create detailed visual plan + variation list
  Node 4: engineer_prompt — Build expert-level prompts for each variation
  Node 5: generate        — Submit to Kaggle GPU (FLUX/CogVideoX)
  Node 6: validate        — Check output quality, retry if needed

ROUTING:
  parse_brief -> analyze_brand -> plan_visual -> engineer_prompt
  -> generate -> validate -> [retry: engineer_prompt | END]

VISUAL ONLY — no text, no captions, no copy.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Annotated, Any, TypedDict

import openai
from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from admin.config import settings
from admin.tools.kaggle_gpu import (
    generate_image,
    generate_video,
    get_platform_size,
)
from admin.tools.visual_tools import discover_brand_identity
from admin.workspace.content_store import WorkspaceContentStore
from admin.workspace.agents.content_templates import (
    PLATFORM_CONFIGS,
    CONTENT_TYPE_CONFIGS,
    STYLE_PRESETS,
    VARIATION_STYLES,
    VIDEO_HUMAN_KEYWORDS,
    VIDEO_AI_AVOID_KEYWORDS,
    IMAGE_PROMPT_TEMPLATE,
    VIDEO_PROMPT_TEMPLATE,
    UGC_VIDEO_PROMPT_TEMPLATE,
    MARKETING_VIDEO_PROMPT_TEMPLATE,
    TRADING_VIDEO_PROMPT_TEMPLATE,
    IMAGE_NEGATIVE_PROMPT,
    VIDEO_NEGATIVE_PROMPT,
    CATEGORY_KEYWORDS,
    detect_content_category,
    detect_platform,
    get_platform_format,
    VIDEO_MOTION_PRESETS,
)

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 3


# ═══════════════════════════════════════════════════════════════════════════════
# CONTENT STORE (per-workspace memory)
# ═══════════════════════════════════════════════════════════════════════════════

_content_store = WorkspaceContentStore()


# ═══════════════════════════════════════════════════════════════════════════════
# STATE
# ═══════════════════════════════════════════════════════════════════════════════

class ContentState(TypedDict):
    # Core conversation
    messages: Annotated[list[dict[str, Any]], "Conversation"]
    workspace_id: str
    workspace_name: str
    client_name: str
    client_website: str
    brand_context: dict[str, Any]
    brief_from: str
    tool_results: Annotated[list[dict[str, Any]], "Tool outputs"]
    current_tool_calls: Annotated[list[dict[str, Any]], "Pending calls"]
    rounds: int

    # Pipeline state
    parsed_brief: dict[str, Any]
    brand_analysis: dict[str, Any]
    visual_plan: dict[str, Any]
    variations: list[dict[str, Any]]
    selected_variation: dict[str, Any] | None
    quality_scores: list[int]
    attempt_count: int
    content_category: str


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def _get_llm_client() -> openai.OpenAI:
    """OpenAI-compatible LLM client (works with Groq, OpenRouter, etc.)."""
    api_key = settings.WORKSPACE_API_KEY or settings.AGENCY_CEO_API_KEY or "dummy"
    base_url = settings.WORKSPACE_API_BASE or settings.AGENCY_CEO_API_BASE or None
    if base_url:
        return openai.OpenAI(api_key=api_key, base_url=base_url)
    return openai.OpenAI(api_key=api_key)


def _load_agency_knowledge(workspace_id: str) -> dict[str, Any]:
    """Load cross-project learnings from Agency Content Agent."""
    try:
        from admin.agency.content_agent import get_agency_content_agent
        agency = get_agency_content_agent()
        return agency.get_knowledge_for_workspace()
    except Exception as e:
        logger.warning("Could not load agency knowledge: %s", e)
        return {}


def _format_brand_context(brand: dict[str, Any]) -> str:
    """Brand context ko human-readable format mein convert karo."""
    if not brand:
        return "No brand info available. Will discover from website if URL provided."

    parts: list[str] = []
    if brand.get("brand_name"):
        parts.append(f"- Brand Name: {brand['brand_name']}")
    if brand.get("colors"):
        parts.append(f"- Brand Colors: {', '.join(brand['colors'][:5])}")
    if brand.get("visual_style"):
        parts.append(f"- Visual Style: {brand['visual_style']}")
    if brand.get("logo_url"):
        parts.append(f"- Logo: {brand['logo_url']}")
    if brand.get("social_links"):
        platforms = list(brand["social_links"].keys())
        parts.append(f"- Social Platforms: {', '.join(platforms)}")
    if brand.get("meta_info", {}).get("description"):
        desc = brand["meta_info"]["description"][:200]
        parts.append(f"- Brand Description: {desc}")

    return "\n".join(parts) if parts else "No brand info available."


def _format_workspace_memory(workspace_id: str) -> str:
    """Workspace ki past learnings load karo."""
    mem = _content_store._memories.get(workspace_id)
    if not mem:
        return "No past work yet — this is the first brief for this workspace."

    parts: list[str] = []
    if mem.brand_learnings:
        parts.append("Brand Learnings:")
        for l_text in mem.brand_learnings[:5]:
            parts.append(f"  - {l_text}")
    if mem.mistakes_to_avoid:
        parts.append("Mistakes to Avoid:")
        for m_text in mem.mistakes_to_avoid[:3]:
            parts.append(f"  - {m_text}")
    if mem.industry_tips:
        parts.append("Industry Tips:")
        for t_text in mem.industry_tips[:3]:
            parts.append(f"  - {t_text}")
    if mem.success_count > 0:
        parts.append(f"Past Successes: {mem.success_count}")
    if mem.failure_count > 0:
        parts.append(f"Past Failures: {mem.failure_count}")

    return "\n".join(parts) if parts else "No past work yet."


def _calculate_quality_score(
    result: dict[str, Any],
    brand_analysis: dict[str, Any],
    parsed_brief: dict[str, Any],
) -> int:
    """Calculate quality score 1-10 for generated output."""
    score = 5  # base

    # File exists and has content?
    file_path = result.get("file", "")
    if file_path and os.path.exists(file_path):
        size = os.path.getsize(file_path)
        if size > 10_000:
            score += 2
        elif size > 0:
            score += 1
        else:
            score -= 2
    else:
        score -= 3

    # Status success?
    if result.get("status") == "success":
        score += 1
    elif result.get("status") in ("error", "submit_failed", "download_error"):
        score -= 2

    # Platform size matches?
    platform = parsed_brief.get("platform", "instagram")
    expected_w, expected_h = get_platform_size(platform)
    size_str = result.get("size", "")
    if size_str:
        try:
            parts = size_str.replace(" frames", "").split("x")
            if len(parts) == 2:
                w, h = int(parts[0]), int(parts[1])
                if abs(w - expected_w) < 50 and abs(h - expected_h) < 50:
                    score += 1
        except (ValueError, IndexError):
            pass

    # Brand colors used? (heuristic: check prompt mentions brand colors)
    prompt_used = result.get("prompt", "")
    primary_colors = brand_analysis.get("primary_colors", [])
    if primary_colors:
        color_mentioned = any(c.lower() in prompt_used.lower() for c in primary_colors[:3])
        if color_mentioned:
            score += 1

    return max(1, min(10, score))


def _llm_call(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.3,
    max_tokens: int = 2000,
) -> str:
    """Simple LLM call — returns assistant content string."""
    client = _get_llm_client()
    model = settings.WORKSPACE_AGENT_MODEL or "llama-3.3-70b-versatile"
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        logger.exception("LLM call failed")
        return f"Error: {e}"


# ═══════════════════════════════════════════════════════════════════════════════
# NODE 1: PARSE BRIEF
# ═══════════════════════════════════════════════════════════════════════════════

def parse_brief(state: ContentState) -> dict[str, Any]:
    """Extract structured brief from raw message using LLM."""
    messages = list(state["messages"])
    user_text = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            user_text = msg.get("content", "")
            break

    system_prompt = (
        "You are a brief parser for a visual content agent. "
        "Extract a structured brief from the user's message. "
        "Return ONLY valid JSON with these fields:\n"
        '{\n'
        '  "visual_type": "image|video|ugc|marketing|trading",\n'
        '  "platform": "instagram|facebook|linkedin|twitter|youtube|tiktok|pinterest|blog_hero",\n'
        '  "format": "post|story|reel|ad|thumbnail|banner|portrait|landscape|square",\n'
        '  "topic": "brief description of the subject",\n'
        '  "mood": "mood/atmosphere words",\n'
        '  "style": "bold|minimal|professional|modern|cinematic|vibrant|elegant|playful",\n'
        '  "color_request": "specific color request or empty string",\n'
        '  "quantity": 3,\n'
        '  "content_category": "fitness|food|realestate|fashion|tech|beauty|travel|education|finance|ecommerce|general",\n'
        '  "priority": "normal|high|urgent"\n'
        '}\n\n'
        "Rules:\n"
        "- visual_type: image for single pictures, video for motion content, "
        "ugc for user-generated content style, marketing for ad/commercial videos, "
        "trading for financial/chart content\n"
        "- platform: detect from context (e.g., 'IG post' = instagram)\n"
        "- format: 'post' unless specifically asked for story/reel/ad\n"
        "- quantity: default 3 for variations, unless specified\n"
        "- Return ONLY the JSON object, no explanation"
    )

    raw_response = _llm_call(system_prompt, user_text)

    # Parse LLM response
    parsed_brief: dict[str, Any] = {}
    try:
        # Try to extract JSON from response
        text = raw_response.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()
        parsed_brief = json.loads(text)
    except (json.JSONDecodeError, IndexError):
        logger.warning("LLM brief parse failed, using fallback detection")
        parsed_brief = {}

    # Fill defaults and validate with keyword detection
    visual_type = parsed_brief.get("visual_type", "image")
    if visual_type not in ("image", "video", "ugc", "marketing", "trading"):
        visual_type = "image"

    platform = parsed_brief.get("platform", "")
    if not platform or platform not in PLATFORM_CONFIGS:
        platform = detect_platform(user_text)

    fmt = parsed_brief.get("format", "")
    if not fmt:
        fmt = get_platform_format(user_text)

    topic = parsed_brief.get("topic", user_text[:200])

    style = parsed_brief.get("style", "professional")
    if style not in STYLE_PRESETS:
        style = "professional"

    mood = parsed_brief.get("mood", "engaging, professional")
    color_request = parsed_brief.get("color_request", "")
    quantity = parsed_brief.get("quantity", 3)
    if not isinstance(quantity, int) or quantity < 1 or quantity > 6:
        quantity = 3

    content_category = parsed_brief.get("content_category", "")
    if not content_category or content_category not in CATEGORY_KEYWORDS:
        content_category = detect_content_category(user_text)

    priority = parsed_brief.get("priority", "normal")
    if priority not in ("normal", "high", "urgent"):
        priority = "normal"

    brief_result = {
        "visual_type": visual_type,
        "platform": platform,
        "format": fmt,
        "topic": topic,
        "mood": mood,
        "style": style,
        "color_request": color_request,
        "quantity": quantity,
        "content_category": content_category,
        "priority": priority,
        "raw_message": user_text,
    }

    return {
        "parsed_brief": brief_result,
        "content_category": content_category,
        "messages": messages,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# NODE 2: ANALYZE BRAND
# ═══════════════════════════════════════════════════════════════════════════════

def analyze_brand(state: ContentState) -> dict[str, Any]:
    """Combine workspace brand context + agency knowledge into brand_analysis."""
    brand = state.get("brand_context", {})
    workspace_id = state.get("workspace_id", "")
    parsed_brief = state.get("parsed_brief", {})

    # Extract primary and secondary colors
    all_colors = brand.get("colors", [])
    primary_colors = all_colors[:3] if all_colors else []
    secondary_colors = all_colors[3:6] if len(all_colors) > 3 else []

    # Visual style
    visual_style = brand.get("visual_style", "professional")

    # Colors to avoid (complementary/opposite of brand for variety, but not clashing)
    do_not_use: list[str] = []
    # If brand has specific colors, avoid completely different aesthetics
    if not all_colors:
        do_not_use = ["neon", "fluorescent"]

    # Platform preferences from brand's social links
    platform_preferences: list[str] = []
    social_links = brand.get("social_links", {})
    if social_links:
        platform_preferences = list(social_links.keys())

    # Agency knowledge
    agency_knowledge = _load_agency_knowledge(workspace_id)

    # Workspace memory
    workspace_memory = _format_workspace_memory(workspace_id)

    brand_analysis = {
        "primary_colors": primary_colors,
        "secondary_colors": secondary_colors,
        "brand_name": brand.get("brand_name", state.get("client_name", "Client")),
        "visual_style": visual_style,
        "do_not_use": do_not_use,
        "platform_preferences": platform_preferences,
        "agency_knowledge": agency_knowledge,
        "workspace_memory": workspace_memory,
        "brand_description": _format_brand_context(brand),
        "logo_url": brand.get("logo_url", ""),
    }

    return {"brand_analysis": brand_analysis}


# ═══════════════════════════════════════════════════════════════════════════════
# NODE 3: PLAN VISUAL
# ═══════════════════════════════════════════════════════════════════════════════

def plan_visual(state: ContentState) -> dict[str, Any]:
    """Create detailed visual plan + variation list from brief + brand analysis."""
    brief = state.get("parsed_brief", {})
    brand = state.get("brand_analysis", {})
    platform = brief.get("platform", "instagram")
    visual_type = brief.get("visual_type", "image")
    fmt = brief.get("format", "post")
    topic = brief.get("topic", "")
    mood = brief.get("mood", "professional")
    style = brief.get("style", "professional")
    quantity = brief.get("quantity", 3)
    color_request = brief.get("color_request", "")

    # Platform dimensions
    platform_cfg = PLATFORM_CONFIGS.get(platform, PLATFORM_CONFIGS["instagram"])
    width, height = platform_cfg["width"], platform_cfg["height"]
    if fmt in platform_cfg.get("variants", {}):
        width, height = platform_cfg["variants"][fmt]

    # Content type config
    ct_cfg = CONTENT_TYPE_CONFIGS.get(visual_type, CONTENT_TYPE_CONFIGS["image"])

    # Style preset
    style_preset = STYLE_PRESETS.get(style, STYLE_PRESETS["professional"])

    # Brand color description
    primary = brand.get("primary_colors", [])
    secondary = brand.get("secondary_colors", [])
    if color_request:
        brand_color_desc = f"Use {color_request} prominently."
    elif primary:
        brand_color_desc = f"Use brand colors: {', '.join(primary)}."
    else:
        brand_color_desc = "Use a professional, modern color palette."

    # Composition/Lighting arrays
    composition_options = [
        "Rule of thirds, subject left, text space right",
        "Centered composition, strong focal point",
        "Diagonal composition, dynamic energy",
        "Symmetrical layout, balanced elements",
    ]
    lighting_options = [
        "Soft natural window light, warm tones",
        "Dramatic side lighting, strong shadows",
        "Even studio lighting, clean and bright",
        "Golden hour ambient light, warm atmosphere",
    ]

    # Video/Motion settings
    motion_description = ""
    motion_key = "slow_zoom"
    if visual_type in ("video", "ugc", "marketing", "trading"):
        motion_description = VIDEO_MOTION_PRESETS.get(motion_key, VIDEO_MOTION_PRESETS["slow_zoom"])["motion"]
    avoid_list = style_preset.get("negative", "")

    # Build visual plan
    visual_plan = {
        "composition": composition_options[hash(topic) % len(composition_options)] if topic else composition_options[0],
        "layout": "modern" if style == "modern" else "clean",
        "elements": [topic] if topic else ["main subject"],
        "color_application": f"{brand_color_desc} Style: {style_preset.get('prompt_suffix', '')}",
        "lighting": lighting_options[hash(mood) % len(lighting_options)] if mood else lighting_options[0],
        "mood_keywords": mood,
        "avoid": avoid_list,
        "text_space": "right side" if "right" in composition_options[0] else "bottom",
        "width": width, "height": height, "platform": platform, "format": fmt,
        "motion_description": motion_description, "motion_key": motion_key,
        "estimated_gpu_time": "30s" if visual_type == "image" else "3-5min",
    }
    if visual_type == "ugc":
        visual_plan["motion_description"] = "handheld, natural, authentic"
        visual_plan["motion_key"] = "handheld"
        visual_plan["environment"] = "natural, real-world setting"
    if visual_type == "trading":
        visual_plan["chart_elements"] = "candlestick charts, moving averages, volume bars"
        visual_plan["motion_description"] = "dynamic data visualization with smooth animations"

    # Create variation plan
    style_keys = list(VARIATION_STYLES.keys())
    variations: list[dict[str, Any]] = []
    for i in range(quantity):
        sk = style_keys[i % len(style_keys)]
        vs = VARIATION_STYLES[sk]
        variations.append({
            "variation_id": f"var_{i+1}", "name": vs["name"], "style_key": sk,
            "prompt_preview": f"{vs['description']} — {topic}",
            "target_platform": platform, "width": width, "height": height,
            "prompt": "", "negative_prompt": "",
            "steps": ct_cfg.get("default_steps", 20) if visual_type == "image" else 0,
            "tool": ct_cfg["tool"], "status": "pending",
        })

    return {
        "visual_plan": visual_plan,
        "variations": variations,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# NODE 4: ENGINEER PROMPT
# ═══════════════════════════════════════════════════════════════════════════════

def engineer_prompt(state: ContentState) -> dict[str, Any]:
    """Build expert-level prompts for each variation."""
    brief = state.get("parsed_brief", {})
    brand = state.get("brand_analysis", {})
    plan = state.get("visual_plan", {})
    variations = list(state.get("variations", []))
    visual_type = brief.get("visual_type", "image")
    platform = brief.get("platform", "instagram")
    topic = brief.get("topic", "")
    mood = brief.get("mood", "professional")
    style = brief.get("style", "professional")
    style_preset = STYLE_PRESETS.get(style, STYLE_PRESETS["professional"])
    primary_colors = brand.get("primary_colors", [])
    color_desc = ", ".join(primary_colors[:3]) if primary_colors else "professional palette"
    avoid = plan.get("avoid", "")
    motion_preset = VIDEO_MOTION_PRESETS.get(plan.get("motion_key", "slow_zoom"), VIDEO_MOTION_PRESETS["slow_zoom"])
    attempt = state.get("attempt_count", 0)

    engineered: list[dict[str, Any]] = []
    for var in variations:
        vs = VARIATION_STYLES.get(var.get("style_key", "hero"), VARIATION_STYLES["hero"])
        add = vs["prompt_addon"]
        brand_line = f"Brand colors: {color_desc}. " if primary_colors else ""
        avoid_line = f"Avoid: {avoid}. " if avoid else ""
        prompt = ""

        if visual_type == "image":
            prompt = (
                f"Professional {style} image of {topic}. {brand_line}"
                f"Composition: {plan.get('composition', '')}. {add} "
                f"Lighting: {plan.get('lighting', '')}. Mood: {mood}. "
                f"{avoid_line}High quality, sharp focus, {platform} optimized, 4K detail."
            )
        elif visual_type == "ugc":
            prompt = (
                f"Authentic UGC-style video of {topic}. Handheld camera, natural lighting, real-person aesthetic. "
                f"Include: {', '.join(VIDEO_HUMAN_KEYWORDS[:5])}. "
                f"Environment: {plan.get('environment', 'natural setting')}. Mood: {mood}. "
                f"Genuine, relatable, unscripted feel. Vertical format, smartphone-quality authenticity."
            )
        elif visual_type == "trading":
            prompt = (
                f"Dynamic financial visualization of {topic}. Charts: {plan.get('chart_elements', 'candlestick')}. "
                f"Colors: {color_desc}. Motion: {motion_preset['motion']}. "
                f"Pacing: {motion_preset['pacing']}. Mood: {mood}. Professional trading aesthetic."
            )
        elif visual_type == "marketing":
            prompt = (
                f"Polished marketing video of {topic}. Brand colors: {color_desc}. "
                f"Motion: {motion_preset['motion']}. Professional commercial look. "
                f"Pacing: {motion_preset['pacing']}. Mood: {mood}. Broadcast-ready."
            )
        else:  # video
            prompt = (
                f"A {motion_preset['motion']} scene featuring {topic}. "
                f"Camera: {motion_preset['camera_move']}. Style: {style}. {brand_line}"
                f"Pacing: {motion_preset['pacing']}. Mood: {mood}. "
                f"Lighting: {plan.get('lighting', '')}. Cinematic quality."
            )

        # Platform tips
        tips = PLATFORM_CONFIGS.get(platform, {}).get("tips", "")
        if tips:
            prompt += f" {tips}"

        # Attempt-based simplification
        if attempt >= 1:
            prompt = ". ".join(prompt.split(". ")[:4]) + f" Style: {style}. High quality."
        if attempt >= 2:
            prompt = f"{style} {visual_type} of {topic}, {color_desc}, high quality, {platform}"

        neg = f"{IMAGE_NEGATIVE_PROMPT}, {style_preset.get('negative', '')}" if visual_type == "image" \
            else f"{VIDEO_NEGATIVE_PROMPT}, {', '.join(VIDEO_AI_AVOID_KEYWORDS[:5])}"

        updated = dict(var)
        updated.update({"prompt": prompt, "negative_prompt": neg, "status": "ready"})
        engineered.append(updated)

    return {"variations": engineered, "attempt_count": state.get("attempt_count", 0) + 1}


# ═══════════════════════════════════════════════════════════════════════════════
# NODE 5: GENERATE
# ═══════════════════════════════════════════════════════════════════════════════

def generate(state: ContentState) -> dict[str, Any]:
    """For each variation, call the appropriate generation tool."""
    variations = list(state.get("variations", []))
    tool_results: list[dict[str, Any]] = list(state.get("tool_results", []))
    attempt = state.get("attempt_count", 0)

    for var in variations:
        if var.get("status") == "completed":
            continue

        prompt = var.get("prompt", "")
        tool_name = var.get("tool", "generate_image")
        width = var.get("width", 1080)
        height = var.get("height", 1080)
        platform = var.get("target_platform", "instagram")
        steps = var.get("steps", 20)

        logger.info(
            "Generating variation %s (%s) [attempt %d]: %s",
            var["variation_id"], tool_name, attempt, prompt[:80],
        )

        result: dict[str, Any] = {}
        try:
            if tool_name == "generate_image" or var.get("tool") == "generate_image":
                # Attempt 2+ fallback to SDXL (fewer steps)
                actual_steps = steps if attempt < 2 else 15
                result = generate_image(
                    prompt=prompt,
                    platform=platform,
                    width=width,
                    height=height,
                    steps=actual_steps,
                )
            else:
                frames = CONTENT_TYPE_CONFIGS.get(
                    state.get("parsed_brief", {}).get("visual_type", "video"),
                    {},
                ).get("default_frames", 49)
                result = generate_video(
                    prompt=prompt,
                    platform=platform,
                    frames=frames,
                )
        except Exception as e:
            logger.exception("Generation failed for variation %s", var["variation_id"])
            result = {"status": "error", "error": str(e)}

        # Track result
        result["variation_id"] = var["variation_id"]
        result["prompt"] = prompt
        tool_results.append({
            "tool": tool_name,
            "variation_id": var["variation_id"],
            "args": {"prompt": prompt, "platform": platform, "width": width, "height": height},
            "result": result,
        })

        # Update variation status
        var["status"] = "completed" if result.get("status") == "success" else "failed"
        var["result"] = result

    return {
        "variations": variations,
        "tool_results": tool_results,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# NODE 6: VALIDATE
# ═══════════════════════════════════════════════════════════════════════════════

def validate(state: ContentState) -> dict[str, Any]:
    """Check quality of each generated output, record to content store."""
    variations = list(state.get("variations", []))
    brand = state.get("brand_analysis", {})
    brief = state.get("parsed_brief", {})
    attempt = state.get("attempt_count", 0)
    workspace_id = state.get("workspace_id", "")

    quality_scores: list[int] = []
    needs_retry = False

    for var in variations:
        result = var.get("result", {})
        if not result:
            quality_scores.append(1)
            needs_retry = True
            continue

        score = _calculate_quality_score(result, brand, brief)
        quality_scores.append(score)

        if score < 5 and attempt < MAX_ATTEMPTS:
            needs_retry = True

        # Record to content store
        if result.get("status") == "success":
            _content_store.record_success(
                workspace_id=workspace_id,
                job_id=result.get("kernel_slug", var.get("variation_id", "")),
                brief_summary=brief.get("topic", "")[:200],
                deliverables=[result.get("file", "")],
                prompts_used=[var.get("prompt", "")],
                platform=brief.get("platform", "instagram"),
                visual_type=brief.get("visual_type", "image"),
                gpu_minutes=result.get("elapsed_seconds", 0) / 60,
                learnings=[f"Variation {var.get('variation_id')}: score={score}"],
            )
        elif result.get("status") in ("error", "submit_failed", "download_error"):
            _content_store.record_failure(
                workspace_id=workspace_id,
                job_id=result.get("kernel_slug", var.get("variation_id", "")),
                brief_summary=brief.get("topic", "")[:200],
                error=result.get("error", "Unknown"),
                platform=brief.get("platform", "instagram"),
                visual_type=brief.get("visual_type", "image"),
                what_failed=f"Variation {var.get('variation_id')}: {result.get('error', 'generation failed')}",
                avoid_next_time=f"Attempt {attempt}: variation {var.get('variation_id')} failed, consider different approach",
            )

    # Update messages with summary
    messages = list(state.get("messages", []))
    success_count = sum(1 for v in variations if v.get("result", {}).get("status") == "success")
    total = len(variations)
    avg_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0

    summary = (
        f"Content generation complete: {success_count}/{total} variations successful. "
        f"Average quality score: {avg_score:.1f}/10. "
        f"Attempt: {attempt}/{MAX_ATTEMPTS}."
    )
    messages.append({"role": "assistant", "content": summary})

    return {
        "quality_scores": quality_scores,
        "messages": messages,
        # Signal retry if needed
        "_needs_retry": needs_retry,
    }


# ═══════════════════════════════════════════════════════════════════════════════

def route_after_validate(state: ContentState) -> str:
    """After validate: retry if needed and under max attempts, else END."""
    needs_retry = state.get("_needs_retry", False)
    attempt = state.get("attempt_count", 0)

    if needs_retry and attempt < MAX_ATTEMPTS:
        logger.info("Retry needed (attempt %d/%d), going back to engineer_prompt", attempt, MAX_ATTEMPTS)
        return "engineer_prompt"

    return END


# ═══════════════════════════════════════════════════════════════════════════════
# LANGGRAPH BUILD
# ═══════════════════════════════════════════════════════════════════════════════

def build_content_graph() -> StateGraph:
    """Build the 6-node content generation pipeline."""
    graph = StateGraph(ContentState)

    # Add nodes
    graph.add_node("parse_brief", parse_brief)
    graph.add_node("analyze_brand", analyze_brand)
    graph.add_node("plan_visual", plan_visual)
    graph.add_node("engineer_prompt", engineer_prompt)
    graph.add_node("generate", generate)
    graph.add_node("validate", validate)

    # Entry point
    graph.set_entry_point("parse_brief")

    # Linear flow: parse -> analyze -> plan -> engineer -> generate -> validate
    graph.add_edge("parse_brief", "analyze_brand")
    graph.add_edge("analyze_brand", "plan_visual")
    graph.add_edge("plan_visual", "engineer_prompt")
    graph.add_edge("engineer_prompt", "generate")
    graph.add_edge("generate", "validate")

    # Conditional edge from validate: retry or END
    graph.add_conditional_edges("validate", route_after_validate, {
        "engineer_prompt": "engineer_prompt",
        END: END,
    })

    return graph.compile(checkpointer=MemorySaver())


_graph = None


def get_content_graph() -> StateGraph:
    """Singleton graph instance."""
    global _graph
    if _graph is None:
        _graph = build_content_graph()
    return _graph


# ═══════════════════════════════════════════════════════════════════════════════
# CONTENT AGENT CLASS
# ═══════════════════════════════════════════════════════════════════════════════

class ContentAgent:
    """Workspace-specific Content Agent — 6-node pipeline for visual content."""

    def __init__(self, workspace_id: str = "", workspace_name: str = "Default",
                 client_name: str = "Client", client_website: str = ""):
        self.workspace_id = workspace_id
        self.workspace_name = workspace_name
        self.client_name = client_name
        self.client_website = client_website
        self.brand: dict[str, Any] = {}
        self._graph = get_content_graph()

        # Load or create memory
        _content_store.get_or_create(
            workspace_id=workspace_id,
            workspace_name=workspace_name,
            client_name=client_name,
        )

        # Auto-discover brand if website provided
        if client_website:
            self.discover_brand(client_website)

    def discover_brand(self, website_url: str = "") -> dict[str, Any]:
        """Client ka brand discover karo website se."""
        url = website_url or self.client_website
        if not url:
            return {}

        logger.info("Discovering brand for %s from %s", self.client_name, url)
        self.brand = discover_brand_identity(url)

        # Save brand info to memory
        mem = _content_store._memories.get(self.workspace_id)
        if mem and self.brand.get("brand_name"):
            if self.brand["brand_name"] not in mem.brand_learnings:
                mem.brand_learnings.append(f"Brand: {self.brand['brand_name']}")
            for color in self.brand.get("colors", [])[:3]:
                learning = f"Brand color: {color}"
                if learning not in mem.brand_learnings:
                    mem.brand_learnings.append(learning)
            if self.brand.get("visual_style"):
                tip = f"Visual style: {self.brand['visual_style']}"
                if tip not in mem.industry_tips:
                    mem.industry_tips.append(tip)
            _content_store._save(self.workspace_id)

        return self.brand

    def run(self, message: str, brief_from: str = "", thread_id: str | None = None) -> dict[str, Any]:
        """Run full 6-node pipeline for a brief."""
        user_msg = f"[Brief from {brief_from}] {message}" if brief_from else message
        initial_state: dict[str, Any] = {
            "messages": [{"role": "user", "content": user_msg}],
            "workspace_id": self.workspace_id, "workspace_name": self.workspace_name,
            "client_name": self.client_name, "client_website": self.client_website,
            "brand_context": self.brand, "brief_from": brief_from,
            "tool_results": [], "current_tool_calls": [], "rounds": 0,
            "parsed_brief": {}, "brand_analysis": {}, "visual_plan": {},
            "variations": [], "selected_variation": None,
            "quality_scores": [], "attempt_count": 0, "content_category": "",
        }
        config = {"configurable": {"thread_id": thread_id or f"content_{self.workspace_id}"}}
        try:
            result = self._graph.invoke(initial_state, config)
            variations = result.get("variations", [])
            successful = [v for v in variations if v.get("result", {}).get("status") == "success"]
            return {
                "success": len(successful) > 0,
                "response": f"Generated {len(successful)}/{len(variations)} variations",
                "variations": variations,
                "tool_results": result.get("tool_results", []),
                "quality_scores": result.get("quality_scores", []),
                "parsed_brief": result.get("parsed_brief", {}),
                "brand_used": self.brand,
                "workspace_name": self.workspace_name,
                "client_name": self.client_name,
                "brief_from": brief_from,
            }
        except Exception as e:
            logger.exception("Content agent pipeline failed")
            return {"success": False, "error": str(e), "response": f"Content Agent error: {e}",
                    "tool_results": [], "variations": []}

    def select_variation(self, variation_id: str) -> dict[str, Any] | None:
        """Select best variation by ID from last run."""
        # This would typically look up from the last run's state
        return {"variation_id": variation_id, "selected": True}

    def status(self) -> dict[str, Any]:
        """Agent status."""
        from admin.tools.kaggle_gpu import _check_kaggle
        mem = _content_store._memories.get(self.workspace_id)
        return {
            "agent": "content",
            "workspace_id": self.workspace_id,
            "workspace_name": self.workspace_name,
            "client_name": self.client_name,
            "client_website": self.client_website,
            "brand_discovered": bool(self.brand),
            "brand_colors": self.brand.get("colors", []),
            "brand_style": self.brand.get("visual_style", ""),
            "kaggle_cli": _check_kaggle(),
            "past_successes": mem.success_count if mem else 0,
            "past_failures": mem.failure_count if mem else 0,
            "pipeline": "6-node (parse->analyze->plan->engineer->generate->validate)",
        }

    def generate_image_direct(
        self, prompt: str, platform: str = "instagram", **kwargs: Any
    ) -> dict[str, Any]:
        """Direct image generation — bypass pipeline."""
        return generate_image(prompt=prompt, platform=platform, **kwargs)

    def generate_video_direct(
        self, prompt: str, platform: str = "instagram", **kwargs: Any
    ) -> dict[str, Any]:
        """Direct video generation — bypass pipeline."""
        return generate_video(prompt=prompt, platform=platform, **kwargs)


# ═══════════════════════════════════════════════════════════════════════════════
# WORKSPACE AGENT REGISTRY
# ═══════════════════════════════════════════════════════════════════════════════

_agents: dict[str, ContentAgent] = {}


def get_or_create_content_agent(
    workspace_id: str,
    workspace_name: str = "",
    client_name: str = "",
    client_website: str = "",
) -> ContentAgent:
    """Get existing Content Agent for workspace, or create new one."""
    if workspace_id in _agents:
        return _agents[workspace_id]

    agent = ContentAgent(
        workspace_id=workspace_id,
        workspace_name=workspace_name or workspace_id,
        client_name=client_name or workspace_name,
        client_website=client_website,
    )
    _agents[workspace_id] = agent
    return agent


def get_content_agent(workspace_id: str) -> ContentAgent | None:
    """Get Content Agent for workspace."""
    return _agents.get(workspace_id)


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════

def run_content_agent(
    message: str,
    workspace_id: str = "",
    workspace_name: str = "",
    client_name: str = "",
    client_website: str = "",
    brief_from: str = "",
    thread_id: str | None = None,
) -> dict[str, Any]:
    """Content Agent ko brief bhejo — auto-creates workspace agent if needed."""
    agent = get_or_create_content_agent(
        workspace_id=workspace_id,
        workspace_name=workspace_name,
        client_name=client_name,
        client_website=client_website,
    )
    return agent.run(
        message=message,
        brief_from=brief_from,
        thread_id=thread_id,
    )
