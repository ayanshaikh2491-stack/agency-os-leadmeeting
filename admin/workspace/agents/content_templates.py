"""Content Templates — Platform configs, prompt templates, and style presets.

Used by the 6-node Content Agent pipeline for consistent visual generation
across all workspaces and platforms.
"""
from __future__ import annotations

from typing import Any


# ═══════════════════════════════════════════════════════════════════════════════
# PLATFORM CONFIGS (size, aspect ratio, best practices per platform)
# ═══════════════════════════════════════════════════════════════════════════════

PLATFORM_CONFIGS: dict[str, dict[str, Any]] = {
    "instagram": {
        "width": 1080,
        "height": 1080,
        "aspect": "1:1",
        "variants": {
            "square": (1080, 1080),
            "portrait": (1080, 1350),
            "story": (1080, 1920),
            "reel": (1080, 1920),
        },
        "video_frames": {"reel": 81, "story": 49},
        "tips": "High contrast, vibrant colors, clean composition, bold text space.",
    },
    "facebook": {
        "width": 1200,
        "height": 630,
        "aspect": "1.91:1",
        "variants": {
            "post": (1200, 630),
            "ad": (1080, 1080),
            "story": (1080, 1920),
            "cover": (820, 312),
        },
        "video_frames": 49,
        "tips": "Warm tones, clear focal point, avoid small text.",
    },
    "linkedin": {
        "width": 1200,
        "height": 627,
        "aspect": "1.91:1",
        "variants": {"post": (1200, 627), "article": (1200, 627)},
        "video_frames": 49,
        "tips": "Professional, corporate, muted tones, clean design.",
    },
    "twitter": {
        "width": 1200,
        "height": 675,
        "aspect": "16:9",
        "variants": {"post": (1200, 675)},
        "video_frames": 49,
        "tips": "Bold, eye-catching, works at small sizes.",
    },
    "youtube": {
        "width": 1280,
        "height": 720,
        "aspect": "16:9",
        "variants": {"thumbnail": (1280, 720), "banner": (2560, 1440)},
        "video_frames": 81,
        "tips": "High contrast thumbnail, face close-ups work well.",
    },
    "tiktok": {
        "width": 1080,
        "height": 1920,
        "aspect": "9:16",
        "variants": {"video": (1080, 1920)},
        "video_frames": 81,
        "tips": "Vertical, dynamic motion, bold colors, fast-paced.",
    },
    "blog_hero": {
        "width": 1200,
        "height": 600,
        "aspect": "2:1",
        "variants": {"hero": (1200, 600), "wide": (1920, 1080)},
        "video_frames": 49,
        "tips": "Wide format, clean left side for text overlay.",
    },
    "pinterest": {
        "width": 1000,
        "height": 1500,
        "aspect": "2:3",
        "variants": {"pin": (1000, 1500)},
        "video_frames": 49,
        "tips": "Tall format, lifestyle imagery, bright colors.",
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# CONTENT TYPE CONFIGS
# ═══════════════════════════════════════════════════════════════════════════════

CONTENT_TYPE_CONFIGS: dict[str, dict[str, Any]] = {
    "image": {
        "tool": "generate_image",
        "default_steps": 20,
        "best_steps": 30,
        "quality_steps": 50,
        "models": ["FLUX.1-dev", "SDXL"],
        "prompt_style": "detailed, descriptive, photographic/artistic language",
    },
    "video": {
        "tool": "generate_video",
        "default_frames": 49,
        "long_frames": 81,
        "models": ["CogVideoX-2b"],
        "prompt_style": "motion-focused, temporal description, scene dynamics",
    },
    "ugc": {
        "tool": "generate_video",
        "default_frames": 81,
        "models": ["CogVideoX-2b"],
        "prompt_style": "authentic, handheld feel, natural lighting, real-person aesthetic",
    },
    "marketing": {
        "tool": "generate_video",
        "default_frames": 49,
        "models": ["CogVideoX-2b"],
        "prompt_style": "polished, commercial, brand-forward, call-to-action space",
    },
    "trading": {
        "tool": "generate_video",
        "default_frames": 49,
        "models": ["CogVideoX-2b"],
        "prompt_style": "dynamic charts, data visualization, financial aesthetics",
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# STYLE PRESETS
# ═══════════════════════════════════════════════════════════════════════════════

STYLE_PRESETS: dict[str, dict[str, str]] = {
    "bold": {
        "prompt_suffix": "bold, high contrast, vivid colors, strong composition, impactful",
        "negative": "faded, washed out, soft, pastel, blurry, low contrast",
    },
    "minimal": {
        "prompt_suffix": "minimalist, clean, white space, elegant, simple composition",
        "negative": "cluttered, busy, noisy, complex, many elements, busy background",
    },
    "professional": {
        "prompt_suffix": "professional, corporate, polished, clean, trustworthy",
        "negative": "amateur, cartoon, childish, messy, unprofessional, low quality",
    },
    "modern": {
        "prompt_suffix": "modern, contemporary, trendy, sleek design, current aesthetics",
        "negative": "retro, vintage, outdated, old-fashioned, dated",
    },
    "cinematic": {
        "prompt_suffix": "cinematic, dramatic lighting, movie-like, depth of field, film grade",
        "negative": "flat lighting, overexposed, underexposed, dull, lifeless",
    },
    "vibrant": {
        "prompt_suffix": "vibrant colors, saturated, energetic, lively, dynamic palette",
        "negative": "desaturated, gray, muted, monochrome, dull colors",
    },
    "elegant": {
        "prompt_suffix": "elegant, refined, luxurious, sophisticated, premium feel",
        "negative": "cheap, tacky, garish, overdone, gaudy",
    },
    "playful": {
        "prompt_suffix": "playful, fun, colorful, lighthearted, engaging",
        "negative": "serious, dark, somber, gloomy, depressing",
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# VARIATION STYLES (for generating multiple prompt variations)
# ═══════════════════════════════════════════════════════════════════════════════

VARIATION_STYLES: dict[str, dict[str, str]] = {
    "hero": {
        "name": "Hero / Focal",
        "description": "Strong central subject, dramatic lighting, hero shot",
        "prompt_addon": "hero shot, central subject, dramatic rim lighting, bold presence, eye-level angle",
    },
    "lifestyle": {
        "name": "Lifestyle / Candid",
        "description": "Natural, in-use, real-world context",
        "prompt_addon": "lifestyle photography, natural setting, candid feel, real-world context, authentic moment",
    },
    "flat_lay": {
        "name": "Flat Lay / Overhead",
        "description": "Top-down view, arranged composition",
        "prompt_addon": "flat lay composition, overhead view, arranged items, clean background, product display",
    },
    "abstract": {
        "name": "Abstract / Artistic",
        "description": "Creative interpretation, artistic style",
        "prompt_addon": "abstract art style, creative interpretation, artistic composition, unique perspective",
    },
    "macro": {
        "name": "Macro / Detail",
        "description": "Close-up, detail focus, texture",
        "prompt_addon": "macro photography, extreme close-up, detailed texture, shallow depth of field, intricate details",
    },
    "aerial": {
        "name": "Aerial / Wide",
        "description": "Wide angle, expansive, landscape feel",
        "prompt_addon": "aerial view, wide angle, expansive landscape, panoramic, bird's eye perspective",
    },
    "dynamic": {
        "name": "Dynamic / Motion",
        "description": "Movement, energy, action",
        "prompt_addon": "dynamic motion, energy, action shot, movement blur, energetic composition",
    },
    "serene": {
        "name": "Serene / Calm",
        "description": "Peaceful, soft, calming",
        "prompt_addon": "serene atmosphere, soft lighting, peaceful, calming mood, gentle tones",
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# VIDEO-SPECIFIC KEYWORDS
# ═══════════════════════════════════════════════════════════════════════════════

VIDEO_HUMAN_KEYWORDS: list[str] = [
    "natural hand movements",
    "subtle facial expressions",
    "authentic body language",
    "casual posture",
    "real person",
    "candid moment",
    "genuine emotion",
    "spontaneous gesture",
    "eye contact",
    "natural smile",
    "handheld camera feel",
    "slight camera shake",
    "warm natural lighting",
    "everyday environment",
    "relatable scenario",
]

VIDEO_AI_AVOID_KEYWORDS: list[str] = [
    "robotic movement",
    "uncanny valley",
    "static pose",
    "perfect symmetry",
    "artificial lighting",
    "stiff gestures",
    "CGI look",
    "3D render",
    "animation style",
    "cartoon",
    "motionless",
    "frozen",
    "unnatural skin",
    "plastic texture",
    "flat shading",
]


# ═══════════════════════════════════════════════════════════════════════════════
# PROMPT TEMPLATES (per content type)
# ═══════════════════════════════════════════════════════════════════════════════

IMAGE_PROMPT_TEMPLATE = (
    "Professional {style} image of {topic}. "
    "{brand_color_desc}"
    "Composition: {composition}. "
    "Lighting: {lighting}. "
    "Mood: {mood}. "
    "Color palette: {color_application}. "
    "{avoid_section}"
    "High quality, sharp focus, {platform} optimized, 4K detail."
)

VIDEO_PROMPT_TEMPLATE = (
    "A {motion_description} scene featuring {topic}. "
    "Camera movement: {camera_move}. "
    "Style: {style}. "
    "{brand_color_desc}"
    "Pacing: {pacing}. "
    "Mood: {mood}. "
    "Lighting: {lighting}. "
    "Smooth motion, professional video quality, cinematic look."
)

UGC_VIDEO_PROMPT_TEMPLATE = (
    "Authentic UGC-style video of {topic}. "
    "Handheld camera feel, natural lighting, casual real-person aesthetic. "
    "{human_keywords}"
    "Environment: {environment}. "
    "Mood: {mood}. "
    "Genuine, relatable, unscripted feel. "
    "Vertical format, natural color grading, smartphone-quality authenticity."
)

MARKETING_VIDEO_PROMPT_TEMPLATE = (
    "Polished marketing video showcasing {topic}. "
    "Brand colors: {brand_colors}. "
    "Motion: {motion_description}. "
    "Professional commercial look, smooth transitions, "
    "clean typography space, {pacing} pacing. "
    "Mood: {mood}. "
    "Studio quality, broadcast-ready, brand-forward presentation."
)

TRADING_VIDEO_PROMPT_TEMPLATE = (
    "Dynamic financial visualization of {topic}. "
    "Animated chart elements: {chart_elements}. "
    "Color scheme: {color_application}. "
    "Motion: {motion_description}. "
    "Professional trading terminal aesthetic, data-driven visualization, "
    "smooth number animations, {pacing} pacing. "
    "Mood: {mood}. Clean, modern financial UI feel."
)


# ═══════════════════════════════════════════════════════════════════════════════
# NEGATIVE PROMPTS
# ═══════════════════════════════════════════════════════════════════════════════

IMAGE_NEGATIVE_PROMPT = (
    "blurry, low quality, pixelated, watermark, text overlay, logo, "
    "distorted, deformed, ugly, overexposed, underexposed, "
    "noise, grain, artifacts, cropped, out of frame, "
    "stock photo feel, generic, bland composition"
)

VIDEO_NEGATIVE_PROMPT = (
    "static, motionless, frozen, jerky movement, stuttering, "
    "low resolution, pixelated, dark, underlit, "
    "robotic motion, unnatural movement, repetitive, "
    "watermark, text, logo, artifacts, noise"
)


# ═══════════════════════════════════════════════════════════════════════════════
# CATEGORY KEYWORDS (for auto-detection)
# ═══════════════════════════════════════════════════════════════════════════════

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "fitness": ["gym", "workout", "fitness", "exercise", "muscle", "training", "health", "wellness"],
    "food": ["restaurant", "food", "cuisine", "dish", "cooking", "recipe", "cafe", "menu"],
    "realestate": ["property", "house", "home", "real estate", "apartment", "interior", "architecture"],
    "fashion": ["fashion", "clothing", "outfit", "style", "wear", "apparel", "brand"],
    "tech": ["software", "app", "technology", "digital", "SaaS", "platform", "AI"],
    "beauty": ["beauty", "skincare", "makeup", "cosmetic", "spa", "wellness"],
    "travel": ["travel", "destination", "vacation", "hotel", "resort", "adventure"],
    "education": ["course", "learn", "education", "training", "class", "tutorial"],
    "finance": ["trading", "stock", "finance", "investment", "crypto", "market", "chart"],
    "ecommerce": ["product", "shop", "store", "sale", "deal", "offer", "buy"],
}


# ═══════════════════════════════════════════════════════════════════════════════
# VIDEO MOTION PRESETS
# ═══════════════════════════════════════════════════════════════════════════════

VIDEO_MOTION_PRESETS: dict[str, dict[str, str]] = {
    "slow_zoom": {
        "motion": "slow zoom into the subject",
        "camera_move": "gentle forward dolly zoom",
        "pacing": "slow, contemplative",
    },
    "pan": {
        "motion": "smooth horizontal pan across the scene",
        "camera_move": "left-to-right pan revealing details",
        "pacing": "steady, measured",
    },
    "orbit": {
        "motion": "circular orbit around the subject",
        "camera_move": "360-degree orbit, parallax movement",
        "pacing": "medium, dynamic",
    },
    "static_reveal": {
        "motion": "elements appearing and building up in frame",
        "camera_move": "locked-off static shot with animated elements",
        "pacing": "gradual buildup",
    },
    "handheld": {
        "motion": "natural handheld camera movement",
        "camera_move": "slight organic shake, documentary-style",
        "pacing": "natural, authentic",
    },
    "tracking": {
        "motion": "tracking shot following the subject",
        "camera_move": "smooth lateral tracking movement",
        "pacing": "fluid, cinematic",
    },
    "whip_pan": {
        "motion": "fast whip pan transition between scenes",
        "camera_move": "rapid horizontal whip",
        "pacing": "fast, energetic",
    },
    "crane": {
        "motion": "crane shot rising up or descending",
        "camera_move": "vertical crane movement, revealing perspective",
        "pacing": "dramatic, building",
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# DETECTION HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def detect_content_category(text: str) -> str:
    """Auto-detect content category from keywords in text."""
    text_lower = text.lower()
    scores: dict[str, int] = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[category] = score
    if scores:
        return max(scores, key=scores.get)  # type: ignore[arg-type]
    return "general"


def detect_platform(text: str) -> str:
    """Auto-detect target platform from keywords in text."""
    text_lower = text.lower()
    platform_signals = {
        "instagram": ["instagram", "insta", "ig ", "reel", "story", "feed post"],
        "facebook": ["facebook", "fb ", "meta ads"],
        "linkedin": ["linkedin", "professional network"],
        "twitter": ["twitter", " x ", "tweet"],
        "youtube": ["youtube", "yt ", "thumbnail", "channel"],
        "tiktok": ["tiktok", "tick", "tok "],
        "pinterest": ["pinterest", "pin "],
        "blog_hero": ["blog", "hero", "banner", "header"],
    }
    for platform, signals in platform_signals.items():
        if any(s in text_lower for s in signals):
            return platform
    return "instagram"  # default


def get_platform_format(text: str) -> str:
    """Detect platform format variant from text."""
    text_lower = text.lower()
    if any(kw in text_lower for kw in ["story", "stories"]):
        return "story"
    if any(kw in text_lower for kw in ["reel", "reels", "short"]):
        return "reel"
    if any(kw in text_lower for kw in ["portrait", "vertical", "tall"]):
        return "portrait"
    if any(kw in text_lower for kw in ["landscape", "wide", "horizontal"]):
        return "landscape"
    if any(kw in text_lower for kw in ["square", "1:1"]):
        return "square"
    if any(kw in text_lower for kw in ["ad", "advertisement", "promotional"]):
        return "ad"
    if any(kw in text_lower for kw in ["thumbnail", "cover"]):
        return "thumbnail"
    return "post"  # default
