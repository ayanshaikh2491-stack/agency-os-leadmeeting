"""Visual Content Tools — brand discovery + visual production for Content Agent.

Content Agent is VISUAL-ONLY. These tools support:
  1. Brand Discovery — auto-scan client's online presence for brand identity
  2. Visual Brief Parser — interpret requests from domain agents
  3. Production Planning — plan what visuals to create
  4. Visual Generation — delegate to Kaggle GPU (FLUX/CogVideo)

Interview Q1: Visual-only execution engine. NO strategy, NO text content.
Interview Q5: Brand discovery — agent self-discovers from social media/website.
Interview Q3: Kaggle API (FLUX for images, CogVideo for videos).
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ═══════════════════════════════════════════════════════════════════════════════
# 1. BRAND DISCOVERY (Interview Q5)
# ═══════════════════════════════════════════════════════════════

def discover_brand_identity(website_url: str) -> dict[str, Any]:
    """Auto-discover client's brand identity from their website.

    Scans for:
    - Logo (og:image, logo class, header images)
    - Color palette (CSS meta theme-color, dominant colors)
    - Brand name (title, og:site_name)
    - Visual style (image types, layout patterns)
    - Social media links

    Interview Q5: "Content Agent ko dimag do — wo khud client ka social media,
    website, existing presence analyze karega"
    """
    result = {
        "website_url": website_url,
        "discovered_at": _now(),
        "brand_name": "",
        "logo_url": "",
        "colors": [],
        "social_links": {},
        "visual_style": "",
        "image_urls": [],
        "meta_info": {},
    }

    try:
        resp = requests.get(website_url, headers=_HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Brand name
        result["brand_name"] = _extract_brand_name(soup)

        # Logo
        result["logo_url"] = _extract_logo(soup, website_url)

        # Colors
        result["colors"] = _extract_colors(soup)

        # Social links
        result["social_links"] = _extract_social_links(soup)

        # Visual style inference
        result["visual_style"] = _infer_visual_style(soup)

        # Sample images
        result["image_urls"] = _extract_sample_images(soup, website_url, limit=10)

        # Meta info
        result["meta_info"] = _extract_meta_info(soup)

    except Exception as e:
        result["error"] = str(e)
        logger.warning("Brand discovery failed for %s: %s", website_url, e)

    return result


def _extract_brand_name(soup: BeautifulSoup) -> str:
    """Extract brand name from various sources."""
    # og:site_name
    og_site = soup.find("meta", property="og:site_name")
    if og_site and og_site.get("content"):
        return og_site["content"].strip()

    # Title tag (strip suffixes like " | Home" or " - Welcome")
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
        for sep in [" | ", " - ", " — ", " :: "]:
            if sep in title:
                return title.split(sep)[0].strip()
        return title

    # Logo alt text
    logo_img = soup.find("img", class_=re.compile(r"logo", re.I))
    if logo_img and logo_img.get("alt"):
        return logo_img["alt"].strip()

    # H1
    h1 = soup.find("h1")
    if h1:
        return h1.get_text(strip=True)[:100]

    return ""


def _extract_logo(soup: BeautifulSoup, base_url: str) -> str:
    """Extract logo URL from page."""
    # og:image
    og_img = soup.find("meta", property="og:image")
    if og_img and og_img.get("content"):
        return og_img["content"]

    # Logo class/id
    for pattern in [r"logo", r"brand"]:
        logo = soup.find("img", class_=re.compile(pattern, re.I))
        if not logo:
            logo = soup.find("img", id=re.compile(pattern, re.I))
        if logo and logo.get("src"):
            return _make_absolute(logo["src"], base_url)

    # First large image in header/nav
    header = soup.find(["header", "nav"])
    if header:
        img = header.find("img")
        if img and img.get("src"):
            return _make_absolute(img["src"], base_url)

    return ""


def _extract_colors(soup: BeautifulSoup) -> list[str]:
    """Extract brand colors from CSS."""
    colors = []

    # theme-color meta
    theme = soup.find("meta", attrs={"name": "theme-color"})
    if theme and theme.get("content"):
        colors.append(theme["content"])

    # Inline style colors (look for hex/rgb in style attributes)
    for tag in soup.find_all(style=True)[:50]:
        style = tag["style"]
        hex_colors = re.findall(r"#(?:[0-9a-fA-F]{3}){1,2}\b", style)
        rgb_colors = re.findall(r"rgb\([^)]+\)", style)
        colors.extend(hex_colors[:2])
        colors.extend(rgb_colors[:1])

    # CSS custom properties in <style> tags
    for style_tag in soup.find_all("style"):
        text = style_tag.string or ""
        css_colors = re.findall(
            r"(?:--[\w-]+)\s*:\s*(#[0-9a-fA-F]{3,8}|rgb[^;]+)", text
        )
        colors.extend(css_colors[:5])

    # Deduplicate, keep first 6
    seen = set()
    unique = []
    for c in colors:
        c_lower = c.lower().strip()
        if c_lower not in seen and len(unique) < 6:
            seen.add(c_lower)
            unique.append(c)
    return unique


def _extract_social_links(soup: BeautifulSoup) -> dict[str, str]:
    """Extract social media profile links."""
    socials = {}
    platforms = {
        "instagram": r"instagram\.com/([^/\s\"'?#]+)",
        "twitter": r"(?:twitter|x)\.com/([^/\s\"'?#]+)",
        "linkedin": r"linkedin\.com/(?:company|in)/([^/\s\"'?#]+)",
        "facebook": r"facebook\.com/([^/\s\"'?#]+)",
        "youtube": r"youtube\.com/(?:@|channel/|c/)([^/\s\"'?#]+)",
        "tiktok": r"tiktok\.com/@([^/\s\"'?#]+)",
        "pinterest": r"pinterest\.(?:com|co)/([^/\s\"'?#]+)",
    }

    for link in soup.find_all("a", href=True):
        href = link["href"]
        for platform, pattern in platforms.items():
            if platform not in socials:
                match = re.search(pattern, href)
                if match:
                    socials[platform] = href if href.startswith("http") else f"https://{href}"

    return socials


def _infer_visual_style(soup: BeautifulSoup) -> str:
    """Infer visual style from page structure."""
    # Count design signals
    images = soup.find_all("img")
    videos = soup.find_all(["video", "iframe"])
    large_headings = sum(1 for h in soup.find_all(["h1", "h2"]) if len(h.get_text(strip=True)) > 30)

    # Check for specific style indicators
    has_dark = bool(soup.find(class_=re.compile(r"dark", re.I)))
    has_minimal = len(images) < 5 and large_headings < 3
    has_bold = any(
        h.get("style", "").lower().find("font-weight") != -1
        or h.get("style", "").lower().find("bold") != -1
        for h in soup.find_all(["h1", "h2"])
    )

    if has_minimal:
        return "minimal"
    if has_dark:
        return "dark/moody"
    if has_bold or len(images) > 15:
        return "bold/visual-heavy"
    if videos:
        return "video-forward"

    return "modern/clean"


def _extract_sample_images(soup: BeautifulSoup, base_url: str, limit: int = 10) -> list[str]:
    """Extract sample images for style reference."""
    images = []
    for img in soup.find_all("img", src=True)[:limit * 2]:
        src = _make_absolute(img["src"], base_url)
        # Filter out tiny icons/tracking pixels
        width = img.get("width", "")
        height = img.get("height", "")
        if width and height:
            try:
                if int(width) < 50 or int(height) < 50:
                    continue
            except (ValueError, TypeError):
                pass
        if any(skip in src.lower() for skip in ["icon", "pixel", "spacer", "1x1"]):
            continue
        images.append(src)
        if len(images) >= limit:
            break
    return images


def _extract_meta_info(soup: BeautifulSoup) -> dict[str, str]:
    """Extract meta information relevant to visual style."""
    meta = {}
    for tag in soup.find_all("meta"):
        name = tag.get("name", "") or tag.get("property", "")
        content = tag.get("content", "")
        if name and content and name in [
            "description", "og:title", "og:description",
            "og:type", "theme-color", "msapplication-TileColor",
        ]:
            meta[name] = content
    return meta


def _make_absolute(url: str, base_url: str) -> str:
    """Convert relative URL to absolute."""
    if url.startswith(("http://", "https://")):
        return url
    parsed = urlparse(base_url)
    if url.startswith("//"):
        return f"{parsed.scheme}:{url}"
    if url.startswith("/"):
        return f"{parsed.scheme}://{parsed.netloc}{url}"
    return f"{parsed.scheme}://{parsed.netloc}/{url}"


# ═══════════════════════════════════════════════════════════════════════════════
# 2. VISUAL BRIEF PARSER
# ═══════════════════════════════════════════════════════════════════════════════

def parse_visual_brief(brief_text: str) -> dict[str, Any]:
    """Parse a visual content brief from a domain agent.

    Extracts:
    - What type of visual is needed (image, video, graphic, etc.)
    - Platform/dimensions
    - Subject/topic
    - Style preferences
    - Quantity
    """
    brief_lower = brief_text.lower()

    # Detect visual type
    visual_type = "image"  # default
    if any(w in brief_lower for w in ["video", "reel", "motion", "animation", "mp4"]):
        visual_type = "video"
    elif any(w in brief_lower for w in ["infographic", "data visualization", "chart"]):
        visual_type = "infographic"
    elif any(w in brief_lower for w in ["carousel", "multiple", "series"]):
        visual_type = "carousel"
    elif any(w in brief_lower for w in ["banner", "hero", "header"]):
        visual_type = "banner"
    elif any(w in brief_lower for w in ["logo", "icon", "brand mark"]):
        visual_type = "logo"

    # Detect platform
    platform = "general"
    platform_map = {
        "instagram": ["instagram", "ig", "reel", "story", "post"],
        "facebook": ["facebook", "fb", "meta"],
        "twitter": ["twitter", "x post", "tweet"],
        "linkedin": ["linkedin", "professional"],
        "youtube": ["youtube", "yt", "thumbnail"],
        "tiktok": ["tiktok", "tt"],
        "pinterest": ["pinterest", "pin"],
        "google": ["google ads", "display ad", "banner ad"],
    }
    for plat, keywords in platform_map.items():
        if any(kw in brief_lower for kw in keywords):
            platform = plat
            break

    # Detect style
    style = "professional"  # default
    style_keywords = {
        "bold": ["bold", "vibrant", "loud", "eye-catching"],
        "minimal": ["minimal", "clean", "simple", "elegant"],
        "creative": ["creative", "artistic", "unique", "quirky"],
        "corporate": ["corporate", "formal", "business", "serious"],
        "playful": ["fun", "playful", "colorful", "friendly"],
    }
    for s, keywords in style_keywords.items():
        if any(kw in brief_lower for kw in keywords):
            style = s
            break

    # Detect quantity
    quantity = 1
    qty_match = re.search(r"(\d+)\s*(?:images?|visuals?|creatives?|pieces?)", brief_lower)
    if qty_match:
        quantity = min(int(qty_match.group(1)), 10)

    return {
        "visual_type": visual_type,
        "platform": platform,
        "style": style,
        "quantity": quantity,
        "raw_brief": brief_text,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 3. PRODUCTION PLANNER
# ═══════════════════════════════════════════════════════════════════════════════

def plan_visual_production(
    brief: dict[str, Any],
    brand_identity: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a visual production plan from a parsed brief.

    Determines:
    - Exact dimensions per platform
    - Prompt engineering for image/video generation
    - Brand-aware style adjustments
    - Estimated GPU time
    """
    platform_sizes = {
        "instagram": (1080, 1080),
        "facebook": (1200, 630),
        "twitter": (1200, 675),
        "linkedin": (1200, 627),
        "youtube": (1280, 720),
        "tiktok": (1080, 1920),
        "pinterest": (1000, 1500),
        "google": (1200, 628),
        "general": (1024, 1024),
    }

    visual_type = brief.get("visual_type", "image")
    platform = brief.get("platform", "general")
    style = brief.get("style", "professional")
    quantity = brief.get("quantity", 1)

    width, height = platform_sizes.get(platform, (1024, 1024))

    # Override for specific types
    if visual_type == "banner":
        width, height = 1920, 1080
    elif visual_type == "infographic":
        width, height = 1080, 1920
    elif visual_type == "video":
        width, height = (1080, 1920) if platform == "tiktok" else (1280, 720)

    # Build generation prompts
    items = []
    for i in range(quantity):
        prompt = _build_generation_prompt(
            brief=brief,
            brand=brand_identity,
            index=i,
            visual_type=visual_type,
        )
        items.append({
            "index": i + 1,
            "type": visual_type,
            "platform": platform,
            "width": width,
            "height": height,
            "prompt": prompt,
            "tool": "generate_video_kaggle" if visual_type == "video" else "generate_image_kaggle",
        })

    # Estimate GPU time
    if visual_type == "video":
        est_minutes = quantity * 5  # ~5 min per video on T4
    else:
        est_minutes = quantity * 1  # ~1 min per image on T4

    return {
        "total_items": len(items),
        "visual_type": visual_type,
        "platform": platform,
        "estimated_gpu_minutes": est_minutes,
        "items": items,
        "brand_applied": bool(brand_identity and brand_identity.get("brand_name")),
    }


def _build_generation_prompt(
    brief: dict[str, Any],
    brand: dict[str, Any] | None,
    index: int,
    visual_type: str,
) -> str:
    """Build an optimized prompt for AI generation."""
    style = brief.get("style", "professional")
    platform = brief.get("platform", "general")
    raw = brief.get("raw_brief", "professional marketing visual")

    style_map = {
        "bold": "bold, vibrant, eye-catching, dynamic colors, high contrast",
        "minimal": "minimalist, clean, elegant, white space, simple",
        "creative": "creative, artistic, unique composition, memorable",
        "corporate": "corporate, professional, business, trustworthy, clean",
        "playful": "fun, playful, colorful, friendly, energetic",
        "professional": "clean, professional, modern, high quality",
    }
    style_desc = style_map.get(style, style_map["professional"])

    # Add brand colors if available
    brand_colors = ""
    if brand and brand.get("colors"):
        brand_colors = f", brand colors: {', '.join(brand['colors'][:3])}"

    # Platform-specific prompt engineering
    platform_hints = {
        "instagram": "Instagram post format, square or portrait, social media ready",
        "facebook": "Facebook ad format, horizontal, engaging",
        "twitter": "Twitter/X post format, landscape, eye-catching",
        "linkedin": "LinkedIn professional post, business-appropriate",
        "youtube": "YouTube thumbnail, bold text space, high contrast",
        "tiktok": "TikTok vertical format, 9:16 aspect ratio, trendy",
        "pinterest": "Pinterest pin, tall vertical, informative",
        "google": "Google Display ad format, clean CTA space",
    }
    platform_hint = platform_hints.get(platform, "professional marketing visual")

    prompt = f"A {style_desc} {visual_type} for {platform_hint}{brand_colors}"
    if raw and raw != "professional marketing visual":
        prompt = f"{raw}, {style_desc}, {platform_hint}{brand_colors}"

    return prompt


# ═══════════════════════════════════════════════════════════════════════════════
# 4. VISUAL TOOL EXECUTION (delegates to Kaggle tools)
# ═══════════════════════════════════════════════════════════════

def execute_visual_tool(tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
    """Execute a visual tool by name."""
    tool_map = {
        "discover_brand_identity": lambda p: discover_brand_identity(p["website_url"]),
        "parse_visual_brief": lambda p: parse_visual_brief(p["brief_text"]),
        "plan_visual_production": lambda p: plan_visual_production(
            brief=p.get("brief", {}),
            brand_identity=p.get("brand_identity"),
        ),
    }
    if tool_name in tool_map:
        return tool_map[tool_name](params)

    # Delegate to Kaggle tools for actual generation
    try:
        from admin.tools.kaggle_tools import execute_kaggle_tool
        return execute_kaggle_tool(tool_name, params)
    except ImportError:
        return {"error": f"Tool '{tool_name}' not found"}


# ═══════════════════════════════════════════════════════════════════════════════
# 5. TOOL DEFINITIONS (for LLM function calling)
# ═══════════════════════════════════════════════════════════════════════════════

VISUAL_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "discover_brand_identity",
            "description": "Scan a client's website to auto-discover brand identity: logo, colors, style, social links. Use when receiving a new client or need brand reference.",
            "parameters": {
                "type": "object",
                "properties": {
                    "website_url": {
                        "type": "string",
                        "description": "Client's website URL to scan",
                    },
                },
                "required": ["website_url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "parse_visual_brief",
            "description": "Parse a visual content brief from a domain agent. Extracts visual type, platform, style, quantity.",
            "parameters": {
                "type": "object",
                "properties": {
                    "brief_text": {
                        "type": "string",
                        "description": "The brief text from a domain agent (SEO, Ads, Social, Website)",
                    },
                },
                "required": ["brief_text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "plan_visual_production",
            "description": "Create a production plan with exact prompts, dimensions, and GPU estimate for visual content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "brief": {
                        "type": "object",
                        "description": "Parsed brief from parse_visual_brief tool",
                    },
                    "brand_identity": {
                        "type": "object",
                        "description": "Brand identity from discover_brand_identity (optional)",
                    },
                },
                "required": ["brief"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_image_kaggle",
            "description": "Generate AI image using FLUX on Kaggle GPU. Free 30hrs/week quota.",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Detailed image description"},
                    "width": {"type": "integer", "description": "Width in pixels", "default": 1024},
                    "height": {"type": "integer", "description": "Height in pixels", "default": 1024},
                    "steps": {"type": "integer", "description": "Inference steps (20-50)", "default": 20},
                },
                "required": ["prompt"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_video_kaggle",
            "description": "Generate AI video using CogVideoX on Kaggle GPU.",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Detailed video description"},
                    "frames": {"type": "integer", "description": "Frames (49=~6s, 81=~10s)", "default": 49},
                },
                "required": ["prompt"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_ad_image",
            "description": "Generate ad creative image sized for specific platform (Facebook, Instagram, Google, etc.)",
            "parameters": {
                "type": "object",
                "properties": {
                    "product": {"type": "string", "description": "Product/service to advertise"},
                    "platform": {"type": "string", "description": "Target platform", "default": "facebook"},
                    "style": {"type": "string", "description": "professional, bold, minimal, creative", "default": "professional"},
                },
                "required": ["product"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_social_image",
            "description": "Generate social media post image for specific platform.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Post topic"},
                    "platform": {"type": "string", "description": "Target platform", "default": "instagram"},
                },
                "required": ["topic"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_hero_image",
            "description": "Generate hero/banner image for website or blog.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Hero image topic"},
                    "style": {"type": "string", "description": "modern, minimal, bold", "default": "modern"},
                },
                "required": ["topic"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_video_ad",
            "description": "Generate video advertisement using CogVideoX on Kaggle.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product": {"type": "string", "description": "Product/service to advertise"},
                    "duration": {"type": "string", "description": "short(6s), medium(10s), long(14s)", "default": "short"},
                },
                "required": ["product"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "batch_generate_images",
            "description": "Generate multiple images for content calendar (up to 5).",
            "parameters": {
                "type": "object",
                "properties": {
                    "topics": {"type": "array", "items": {"type": "string"}, "description": "List of topics"},
                    "platform": {"type": "string", "description": "Target platform", "default": "instagram"},
                },
                "required": ["topics"],
            },
        },
    },
]
