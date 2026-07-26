# Content Agent Advanced Implementation Plan

> **For agentic workers:** Use subagent-driven-development or executing-plans to implement this plan task-by-task.

**Goal:** Rebuild Content Agent into a 6-node LangGraph pipeline with variations, quality scoring, error recovery, UGC/marketing video support, and cross-project agency knowledge.

**Architecture:** Single LangGraph pipeline with 6 nodes (parse_brief, analyze_brand, plan_visual, engineer_prompt, generate, validate). Each node is a pure function operating on ContentState. Variation system generates 3-4 outputs per brief. Agency knowledge injects cross-project learnings into Node 2.

**Tech Stack:** Python 3.13, LangGraph, OpenAI API, Kaggle CLI (FLUX/CogVideoX), BeautifulSoup (brand discovery)

## Global Constraints
- VISUAL ONLY — no text, captions, copy
- Python 3.13+, type hints everywhere
- LangGraph StateGraph for pipeline
- Kaggle GPU for generation (FLUX images, CogVideoX videos)
- Per-workspace isolation (data/workspaces/{id}/)
- All outputs go through CEO approval before delivery

## File Structure

| File | Responsibility |
|------|---------------|
| `admin/workspace/agents/content.py` | Main pipeline (6 nodes), ContentAgent class, variation system |
| `admin/workspace/agents/content_templates.py` | Prompt templates, platform configs, content type definitions |
| `admin/workspace/content_store.py` | Enhanced memory: variations, quality scores, style history |
| `admin/tools/kaggle_gpu.py` | Add smart_retry, generate_with_fallback, batch_generate |
| `admin/tools/visual_tools.py` | Add UGC tools, marketing video tools, competitor analysis |
| `admin/agency/content_agent.py` | Add inject_knowledge, record_pattern, get_industry_insights |
| `admin/api/routes/content.py` | Add variation, UGC, marketing, batch endpoints |
| `admin/tests/test_content_agent.py` | Tests for all nodes, pipeline, variations |

---

## Task 1: Content Templates + Constants

**Files:**
- Create: `admin/workspace/agents/content_templates.py`

**Interfaces:**
- Produces: `PLATFORM_CONFIGS`, `CONTENT_TYPE_CONFIGS`, `STYLE_PRESETS`, `PROMPT_TEMPLATES`, `VIDEO_HUMAN_KEYWORDS`

- [ ] **Step 1: Create content_templates.py**

```python
"""Content Agent — Templates, constants, and configuration.

Platform sizes, style presets, prompt templates, content type configs.
All visual-only — no text/caption/copy definitions here.
"""
from __future__ import annotations

from typing import Any


# ── Platform Configs ─────────────────────────────────────────────────────────

PLATFORM_CONFIGS: dict[str, dict[str, Any]] = {
    "instagram": {
        "post": {"width": 1080, "height": 1350, "format": "portrait"},
        "story": {"width": 1080, "height": 1920, "format": "vertical"},
        "reel_cover": {"width": 1080, "height": 1920, "format": "vertical"},
        "ad": {"width": 1080, "height": 1080, "format": "square"},
        "style_hint": "Bold, vibrant, high contrast, social media ready",
    },
    "facebook": {
        "post": {"width": 1200, "height": 630, "format": "horizontal"},
        "ad": {"width": 1080, "height": 1080, "format": "square"},
        "story": {"width": 1080, "height": 1920, "format": "vertical"},
        "style_hint": "Clean, engaging, balanced composition",
    },
    "linkedin": {
        "post": {"width": 1200, "height": 627, "format": "horizontal"},
        "ad": {"width": 1200, "height": 627, "format": "horizontal"},
        "style_hint": "Professional, muted tones, corporate feel",
    },
    "twitter": {
        "post": {"width": 1200, "height": 675, "format": "horizontal"},
        "style_hint": "Bold, contrast, quick visual impact",
    },
    "youtube": {
        "thumbnail": {"width": 1280, "height": 720, "format": "landscape"},
        "shorts": {"width": 1080, "height": 1920, "format": "vertical"},
        "style_hint": "Bold text space, high contrast, clickable",
    },
    "tiktok": {
        "post": {"width": 1080, "height": 1920, "format": "vertical"},
        "style_hint": "Trendy, fast, energetic, full-screen",
    },
    "pinterest": {
        "pin": {"width": 1000, "height": 1500, "format": "vertical"},
        "style_hint": "Tall vertical, informative, aspirational",
    },
    "blog_hero": {
        "hero": {"width": 1200, "height": 600, "format": "landscape"},
        "og_image": {"width": 1200, "height": 630, "format": "horizontal"},
        "style_hint": "Clean, minimal, wide format",
    },
    "google_ads": {
        "display": {"width": 1200, "height": 628, "format": "horizontal"},
        "square": {"width": 300, "height": 250, "format": "banner"},
        "style_hint": "Clean CTA space, product focused",
    },
}


# ── Content Type Configs ─────────────────────────────────────────────────────

CONTENT_TYPE_CONFIGS: dict[str, dict[str, Any]] = {
    "social_image": {
        "tool": "generate_image",
        "default_platform": "instagram",
        "default_format": "post",
    },
    "ad_image": {
        "tool": "generate_image",
        "default_platform": "facebook",
        "default_format": "ad",
    },
    "hero_image": {
        "tool": "generate_image",
        "default_platform": "blog_hero",
        "default_format": "hero",
    },
    "social_video": {
        "tool": "generate_video",
        "default_platform": "instagram",
        "default_format": "reel",
    },
    "ad_video": {
        "tool": "generate_video",
        "default_platform": "facebook",
        "default_format": "ad",
    },
    "ugc_video": {
        "tool": "generate_video",
        "default_platform": "instagram",
        "default_format": "reel",
    },
    "marketing_video": {
        "tool": "generate_video",
        "default_platform": "youtube",
        "default_format": "shorts",
    },
    "trading_video": {
        "tool": "generate_video",
        "default_platform": "youtube",
        "default_format": "shorts",
    },
    "batch_images": {
        "tool": "generate_image",
        "default_platform": "instagram",
        "default_format": "post",
    },
}


# ── Style Presets ────────────────────────────────────────────────────────────

STYLE_PRESETS: dict[str, str] = {
    "bold": "bold, vibrant, eye-catching, dynamic colors, high contrast, energetic",
    "minimal": "minimalist, clean, elegant, white space, simple, refined",
    "creative": "creative, artistic, unique composition, memorable, unconventional",
    "corporate": "corporate, professional, business, trustworthy, clean, structured",
    "playful": "fun, playful, colorful, friendly, energetic, warm",
    "dramatic": "dramatic, cinematic, moody, strong shadows, intense atmosphere",
    "modern": "modern, clean, contemporary, sleek, sophisticated",
    "raw": "raw, gritty, authentic, industrial, unpolished, real",
    "lifestyle": "lifestyle, everyday, approachable, warm, natural, relatable",
    "professional": "clean, professional, modern, high quality, polished",
}


# ── Variation Style Names ────────────────────────────────────────────────────

VARIATION_STYLES = [
    {
        "name": "Bold & Dramatic",
        "style_key": "dramatic",
        "mood": "intense, powerful, high-contrast",
        "description": "Dark tones, dramatic lighting, strong shadows, cinematic feel",
    },
    {
        "name": "Clean & Modern",
        "style_key": "modern",
        "mood": "professional, aspirational, bright",
        "description": "Clean background, natural light, professional finish",
    },
    {
        "name": "Raw & Authentic",
        "style_key": "raw",
        "mood": "authentic, gritty, real",
        "description": "Industrial feel, natural imperfections, genuine atmosphere",
    },
    {
        "name": "Lifestyle Focus",
        "style_key": "lifestyle",
        "mood": "approachable, warm, everyday",
        "description": "Real-world setting, natural moments, relatable feel",
    },
]


# ── Video Human-Like Keywords ────────────────────────────────────────────────

VIDEO_HUMAN_KEYWORDS = (
    "cinematic, natural lighting, handheld camera feel, "
    "warm color grading, real environment, authentic, "
    "documentary style, 24fps film look, subtle lens flare, "
    "organic movement, genuine expressions"
)

VIDEO_AI_AVOID_KEYWORDS = (
    "perfect symmetry, robotic motion, stock footage, "
    "over-saturated, static background,CGI, rendered, "
    "artificial, synthetic, studio backdrop"
)


# ── Prompt Templates ─────────────────────────────────────────────────────────

IMAGE_PROMPT_TEMPLATE = (
    "A {style_desc} {subject} for {platform_hint}, "
    "{mood} atmosphere, {color_instruction}, "
    "composition: {composition}, lighting: {lighting}, "
    "quality: professional, 4k ultra detailed"
)

VIDEO_PROMPT_TEMPLATE = (
    "A {style_desc} {content_type} video of {subject}, "
    "{motion_description}, {mood} atmosphere, "
    "{color_instruction}, {human_keywords}, "
    "quality: cinematic, high production value"
)

UGC_VIDEO_PROMPT_TEMPLATE = (
    "A natural, authentic user-generated content style video of {subject}, "
    "{motion_description}, casual feel, "
    "handheld camera, natural lighting from window, "
    "warm color grading, real office/home environment, "
    "genuine expressions, documentary style, 24fps film look"
)

MARKETING_VIDEO_PROMPT_TEMPLATE = (
    "A professional marketing video showcasing {subject}, "
    "{motion_description}, {mood} atmosphere, "
    "{color_instruction}, smooth transitions, "
    "product-focused cinematography, high production value"
)

TRADING_VIDEO_PROMPT_TEMPLATE = (
    "A professional financial/trading video with {subject}, "
    "animated charts and data visualization, "
    "{motion_description}, clean professional style, "
    "data-driven graphics, {mood} atmosphere, "
    "like a real financial analyst presentation"
)


# ── Negative Prompts ─────────────────────────────────────────────────────────

IMAGE_NEGATIVE_PROMPT = (
    "blurry, stock photo feel, cluttered, text, watermark, "
    "low quality, overexposed, underexposed, distorted, "
    "artificial, CGI look, bad anatomy"
)

VIDEO_NEGATIVE_PROMPT = (
    "robotic motion, perfect symmetry, stock footage, "
    "over-saturated, static, artificial, synthetic, "
    "CGI look, bad timing, choppy"
)


# ── Content Category Detection Keywords ──────────────────────────────────────

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "trading": ["trading", "chart", "candlestick", "stock", "finance", "crypto", "market", "price", "investing"],
    "ugc": ["testimonial", "review", "unboxing", "reaction", "user generated", "ugc", "authentic", "real person"],
    "product_review": ["product review", "showcase", "360", "feature", "hands-on", "demo"],
    "project_review": ["project review", "portfolio", "case study", "before after", "transformation", "process"],
    "marketing": ["marketing", "product launch", "promo", "advertisement", "brand story", "explainer"],
    "ad": ["ad", "advertisement", "ad creative", "ad campaign", "paid", "display ad"],
    "social": ["post", "social media", "reel", "story", "engagement", "community"],
    "hero": ["hero", "banner", "header", "cover", "thumbnail"],
}


def detect_content_category(brief_text: str) -> str:
    """Detect content category from brief text."""
    text_lower = brief_text.lower()
    scores: dict[str, int] = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[category] = score
    if scores:
        return max(scores, key=scores.get)
    return "social"


# ── Platform Detection ───────────────────────────────────────────────────────

PLATFORM_KEYWORDS: dict[str, list[str]] = {
    "instagram": ["instagram", "ig", "reel", "story", "post", "feed"],
    "facebook": ["facebook", "fb", "meta"],
    "twitter": ["twitter", "x post", "tweet"],
    "linkedin": ["linkedin", "professional", "business"],
    "youtube": ["youtube", "yt", "thumbnail", "shorts"],
    "tiktok": ["tiktok", "tt"],
    "pinterest": ["pinterest", "pin"],
    "google_ads": ["google ads", "display ad", "banner ad"],
    "blog_hero": ["blog", "hero", "banner", "header", "og image"],
}


def detect_platform(brief_text: str) -> str:
    """Detect target platform from brief text."""
    text_lower = brief_text.lower()
    for platform, keywords in PLATFORM_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return platform
    return "instagram"


def get_platform_format(platform: str, brief_text: str) -> str:
    """Get specific format for a platform from brief text."""
    text_lower = brief_text.lower()
    pcfg = PLATFORM_CONFIGS.get(platform, {})
    for fmt_key in pcfg:
        if fmt_key in ("style_hint",):
            continue
        if fmt_key in text_lower:
            return fmt_key
    formats = [k for k in pcfg if k != "style_hint"]
    return formats[0] if formats else "post"

