"""SEO Agent Skills — loaded from Jcode's skill catalog.

Relevant skills are auto-detected from the message and passed as context
so the SEO agent can apply SEO strategies and frameworks.

Supports SEO (ranking), SEO-technical (audits), AEO (Answer Engine
Optimization — ranking inside AI answers like ChatGPT/Perplexity/Gemini),
and GEO (Generative Engine Optimization — being cited by AI search engines).

Skill content is loaded from either ~/.jcode/skills or ~/.agents/skills
(the directory name per registry entry is given by ``dir``; defaults to the
registry ``name`` when ``dir`` is omitted).
"""
from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

JCODE_SKILLS_DIR = Path.home() / ".jcode" / "skills"
AGENTS_SKILLS_DIR = Path.home() / ".agents" / "skills"

SEO_SKILL_REGISTRY: list[dict] = [
    {
        "name": "seo",
        "dir": "seo",
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
        "name": "seo-technical",
        "dir": "seo-technical",
        "keywords": [
            "technical seo", "technical audit", "crawl budget",
            "canonical", "hreflang", "render", "javascript seo",
            "site architecture", "xml sitemap", "robots",
            "structured data validation", "schema validation",
        ],
        "description": "Technical SEO deep-dive -- crawlability, render, canonicalization, site architecture",
    },
    {
        "name": "aeo",
        "dir": "seo-aeo-best-practices",
        "keywords": [
            "answer engine optimization", "aeo", "ai overview",
            "chatgpt", "perplexity", "gemini", "ai search",
            "ai answer", "featured snippet", "people also ask",
            "knowledge graph", "knowledge panel", "entity seo",
            "schema for ai", "llm optimization", "ai mode",
            "answer box", "position zero",
        ],
        "description": "Answer Engine Optimization -- get the business cited/ranked inside AI answers (ChatGPT, Perplexity, Gemini, AI Overviews)",
    },
    {
        "name": "geo",
        "dir": "seo-geo",
        "keywords": [
            "generative engine optimization", "geo", "generative search",
            "ai citation", "cited by ai", "llm visibility",
            "ai search engine", "ai recommend", "ai mentions",
            "generative engine", "ai brand visibility",
            "chatgpt recommendation", "ai overview citation",
        ],
        "description": "Generative Engine Optimization -- be the source AI search engines cite and recommend",
    },
    {
        "name": "content-engine",
        "dir": "content-engine",
        "keywords": [
            "blog", "article", "content strategy", "content calendar",
            "repurpose", "content gap", "pillar content",
            "topic cluster", "content brief", "writer",
        ],
        "description": "Content strategy -- blog writing, repurposing, topic clusters, content briefs",
    },
    {
        "name": "seo-audit",
        "dir": "seo-technical",
        "keywords": [
            "audit", "site audit", "technical audit", "seo audit",
            "broken link", "404", "redirect", "canonical",
            "sitemap", "robots.txt", "crawl error",
            "page speed",
        ],
        "description": "Technical SEO audit -- site crawl, broken links, redirects, sitemap analysis",
    },
]


def _load_skill_content(skill_name: str, skill_dir: str | None = None) -> str | None:
    dirname = skill_dir or skill_name
    for base in (JCODE_SKILLS_DIR, AGENTS_SKILLS_DIR):
        skill_path = base / dirname / "SKILL.md"
        if skill_path.is_file():
            try:
                return skill_path.read_text(encoding="utf-8")
            except Exception as e:  # noqa: BLE001 - never crash on skill load
                logger.error("Error reading skill %s: %s", skill_name, e)
                return None
    return None


def detect_skills(message: str, max_skills: int = 3) -> list[dict]:
    msg_lower = message.lower()
    matched: list[dict] = []
    seen: set[str] = set()
    for skill in SEO_SKILL_REGISTRY:
        if skill["name"] in seen:
            continue
        for kw in skill["keywords"]:
            if kw in msg_lower:
                content = _load_skill_content(skill["name"], skill.get("dir"))
                matched.append({
                    "name": skill["name"],
                    "description": skill["description"],
                    "content": content or f"Skill: {skill['name']} - {skill['description']}",
                })
                seen.add(skill["name"])
                break
        if len(matched) >= max_skills:
            break
    return matched


MAX_SKILL_CONTENT_CHARS = 2000
MAX_TOTAL_SKILL_CHARS = 5000


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
