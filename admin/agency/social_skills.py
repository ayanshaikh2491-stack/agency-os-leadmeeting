# admin/agency/social_skills.py
"""Social Agent Skills — loaded from Jcode's skill catalog.

Mirrors sba_skills.py / seo_skills.py / website_skills.py. Relevant skills
are auto-detected from the message and passed as context so the Social
Agent can apply real marketing, copywriting, and content frameworks.
"""
from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

JCODE_SKILLS_DIR = Path.home() / ".jcode" / "skills"
AGENTS_SKILLS_DIR = Path.home() / ".agents" / "skills"

SOCIAL_SKILL_REGISTRY: list[dict] = [
    {
        "name": "ad-creative",
        "keywords": [
            "ad copy", "ad creative", "headline", "rsa", "facebook ad",
            "google ad", "ad variations", "hook writing", "creative strategy",
        ],
        "description": "Generate and iterate paid ad creative (headlines, descriptions, primary text)",
    },
    {
        "name": "social",
        "keywords": [
            "linkedin post", "twitter thread", "instagram", "social media",
            "content calendar", "viral", "what should i post", "reel", "carousel",
            "caption", "post ideas", "social strategy", "hashtag",
        ],
        "description": "Social media content creation, scheduling, and strategy",
    },
    {
        "name": "content-engine",
        "keywords": [
            "content system", "content plan", "repurpose", "multi-platform",
            "content pipeline", "newsletter", "youtube script",
        ],
        "description": "Platform-native content systems and repurposing",
    },
    {
        "name": "post-writer-sms",
        "keywords": [
            "write a post", "post for me", "draft post", "engagement post",
            "cta post", "announcement post",
        ],
        "description": "Write platform-native social posts",
    },
    {
        "name": "brand-voice",
        "keywords": [
            "brand voice", "tone of voice", "writing style", "voice profile",
            "consistent voice", "copy style",
        ],
        "description": "Build a source-derived writing style profile",
    },
    {
        "name": "content-calendar-sms",
        "keywords": [
            "content calendar", "posting schedule", "when to post",
            "content cadence", "weekly plan", "monthly content plan",
        ],
        "description": "Plan social media posting schedules and calendars",
    },
]

MAX_SKILL_CONTENT_CHARS = 2000
MAX_TOTAL_SKILL_CHARS = 4000


def _load_skill_content(skill_name: str) -> str | None:
    for base in (JCODE_SKILLS_DIR, AGENTS_SKILLS_DIR):
        f = base / skill_name / "SKILL.md"
        if f.exists():
            try:
                return f.read_text(encoding="utf-8", errors="ignore")[:MAX_SKILL_CONTENT_CHARS]
            except OSError:
                continue
    return None


def detect_skills(message: str, max_skills: int = 2) -> list[dict]:
    msg_lower = message.lower()
    hits = []
    for skill in SOCIAL_SKILL_REGISTRY:
        if any(kw in msg_lower for kw in skill["keywords"]):
            content = _load_skill_content(skill["name"])
            if content:
                hits.append({**skill, "content": content})
            else:
                hits.append({**skill, "content": ""})
        if len(hits) >= max_skills:
            break
    return hits


def build_skill_context(skills: list[dict]) -> str:
    parts = []
    total = 0
    for s in skills:
        content = s.get("content", "") or s.get("description", "")
        if not content:
            continue
        block = f"### {s['name']}\n{content}"
        if total + len(block) > MAX_TOTAL_SKILL_CHARS:
            block = block[: MAX_TOTAL_SKILL_CHARS - total]
        parts.append(block)
        total += len(block)
        if total >= MAX_TOTAL_SKILL_CHARS:
            break
    return "\n\n".join(parts)


def list_social_skills() -> list[dict]:
    out = []
    for s in SOCIAL_SKILL_REGISTRY:
        out.append({"name": s["name"], "description": s["description"], "keywords": s["keywords"]})
    return out
