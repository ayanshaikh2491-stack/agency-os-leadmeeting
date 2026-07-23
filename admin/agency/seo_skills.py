"""SEO Agent Skills — loaded from Jcode's skill catalog.

Relevant skills are auto-detected from the message and passed as context
so the SEO agent can apply SEO strategies and frameworks.
"""
from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

JCODE_SKILLS_DIR = Path.home() / ".jcode" / "skills"

SEO_SKILL_REGISTRY: list[dict] = [
    {
        "name": "seo",
        "keywords": [
            "seo", "search engine optimization", "ranking", "serp",
            "backlink", "link building", "domain authority",
            "keyword research", "on-page seo", "off-page seo",
            "technical seo", "site audit", "crawl", "indexing",
            "meta tag", "title tag", "schema markup", "structured data",
            "core web vitals", "page speed", "mobile seo",
            "local seo", "google business profile",
            "content optimization", "internal linking",
        ],
        "description": "Full-stack SEO strategy -- technical audits, keyword research, on-page/off-page, local SEO",
    },
    {
        "name": "content-engine",
        "keywords": [
            "blog", "article", "content strategy", "content calendar",
            "repurpose", "content gap", "pillar content",
            "topic cluster", "content brief", "writer",
        ],
        "description": "Content strategy -- blog writing, repurposing, topic clusters, content briefs",
    },
    {
        "name": "seo-audit",
        "keywords": [
            "audit", "site audit", "technical audit", "seo audit",
            "broken link", "404", "redirect", "canonical",
            "sitemap", "robots.txt", "crawl error",
            "page speed",
        ],
        "description": "Technical SEO audit -- site crawl, broken links, redirects, sitemap analysis",
    },
]


def _load_skill_content(skill_name: str) -> str | None:
    skill_path = JCODE_SKILLS_DIR / skill_name / "SKILL.md"
    if not skill_path.is_file():
        return None
    try:
        return skill_path.read_text(encoding="utf-8")
    except Exception as e:
        logger.error("Error reading skill %s: %s", skill_name, e)
        return None


def detect_skills(message: str, max_skills: int = 2) -> list[dict]:
    msg_lower = message.lower()
    matched: list[dict] = []
    for skill in SEO_SKILL_REGISTRY:
        for kw in skill["keywords"]:
            if kw in msg_lower:
                content = _load_skill_content(skill["name"])
                matched.append({
                    "name": skill["name"],
                    "description": skill["description"],
                    "content": content or f"Skill: {skill['name']} - {skill['description']}",
                })
                break
        if len(matched) >= max_skills:
            break
    return matched


MAX_SKILL_CONTENT_CHARS = 2000
MAX_TOTAL_SKILL_CHARS = 4000


def build_skill_context(skills: list[dict]) -> str:
    if not skills:
        return ""
    blocks: list[str] = []
    total_chars = 0
    for s in skills:
        content = s["content"]
        if len(content) > MAX_SKILL_CONTENT_CHARS:
            content = content[:MAX_SKILL_CONTENT_CHARS] + "\n...[truncated]"
        if total_chars + len(content) > MAX_TOTAL_SKILL_CHARS:
            break
        total_chars += len(content)
        blocks.append(
            f"### Skill: {s['name']}\n"
            f"{s['description']}\n\n"
            f"{content}"
        )
    if not blocks:
        return ""
    return (
        "-- RELEVANT SEO SKILLS --\n"
        + "\n\n".join(blocks)
        + "\n----------------------------------------------"
    )


def list_seo_skills() -> list[dict]:
    return [
        {"name": s["name"], "description": s["description"], "keywords": s["keywords"]}
        for s in SEO_SKILL_REGISTRY
    ]


# Backward compat alias
detect_seo_skills = detect_skills
