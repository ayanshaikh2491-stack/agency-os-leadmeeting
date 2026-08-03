"""Website Agent Skills — loaded from Jcode's skill catalog.

Each skill is a SKILL.md file in ~/.jcode/skills/<skill-name>/ (or
~/.agents/skills/<skill-name>/ as a fallback). Relevant skills are
auto-detected from the message and passed as context so the Website
Agent can apply real web design, frontend, and deployment frameworks.

Mirrors sba_skills.py / seo_skills.py.
"""
from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Skill directories (Jcode first, agents catalog as fallback) ─────────
JCODE_SKILLS_DIR = Path.home() / ".jcode" / "skills"
AGENTS_SKILLS_DIR = Path.home() / ".agents" / "skills"

# ── Website-relevant skills (design, frontend, deploy) ──────────────────
WEBSITE_SKILL_REGISTRY: list[dict] = [
    # ── Design direction ────────────────────────────────────────────
    {
        "name": "frontend-design",
        "keywords": [
            "design", "layout", "visual", "typography", "aesthetic",
            "look and feel", "beautiful", "modern design", "clean design",
            "landing page design", "website design", "ui design",
        ],
        "description": "Distinctive, intentional visual design — aesthetic direction, typography, non-templated choices",
    },
    {
        "name": "frontend-design-direction",
        "keywords": [
            "design direction", "brand feel", "design language",
            "product ui", "dashboard design", "app design",
        ],
        "description": "Set a product-specific frontend design direction for production UI work",
    },
    {
        "name": "design-taste-frontend",
        "keywords": [
            "redesign", "portfolio", "anti-slop", "templated", "unique design",
            "stand out", "modern website", "fresh look",
        ],
        "description": "Anti-slop frontend design for landing pages, portfolios, and redesigns",
    },
    {
        "name": "hallmark",
        "keywords": [
            "slop", "greenfield", "design audit", "design extraction",
            "make it premium", "high-end", "signature style",
        ],
        "description": "Anti-AI-slop design system for greenfield pages, audits, redesigns, and style extraction",
    },
    {
        "name": "impeccable",
        "keywords": [
            "polish", "refine", "audit ui", "ux review", "improve ui",
            "harden", "polish interface", "visual hierarchy", "micro-interaction",
        ],
        "description": "Design/redesign/audit/polish frontend interfaces — UX, hierarchy, motion, accessibility",
    },
    {
        "name": "design-system",
        "keywords": [
            "design system", "design tokens", "component system",
            "visual consistency", "design review", "styling audit",
        ],
        "description": "Generate or audit design systems and check visual consistency",
    },
    {
        "name": "ui-ux-pro-max",
        "keywords": [
            "color palette", "font pairing", "ux guidelines", "chart types",
            "gsap motion", "animation preset", "ui style", "ui intelligence",
        ],
        "description": "UI/UX design intelligence — styles, color palettes, font pairings, UX guidelines, motion presets",
    },
    {
        "name": "theme-factory",
        "keywords": [
            "theme", "theming", "color scheme", "brand colors",
            "style artifact", "slide theme", "report theme",
        ],
        "description": "Style artifacts with a theme — 10 pre-set themes with colors/fonts or generate on-the-fly",
    },
    # ── Frontend frameworks ──────────────────────────────────────────
    {
        "name": "nextjs-developer",
        "keywords": [
            "nextjs", "next.js", "app router", "server components",
            "rsc", "vercel deploy", "ssr", "middleware", "route handler",
        ],
        "description": "Build Next.js 14+ apps — App Router, server components, server actions, Vercel deploy",
    },
    {
        "name": "react-expert",
        "keywords": [
            "react", "react.js", "reactjs", "hooks", "usestate",
            "component", "jsx", "tsx", "state management", "suspense",
        ],
        "description": "Build React 18+ apps — components, custom hooks, state, performance",
    },
    {
        "name": "senior-frontend",
        "keywords": [
            "tailwind", "typescript", "frontend performance", "bundle size",
            "accessibility", "responsive", "scaffold", "optimize frontend",
        ],
        "description": "Senior frontend — React/Next/TypeScript/Tailwind, performance, a11y, scaffolding",
    },
    {
        "name": "react-best-practices",
        "keywords": [
            "react best practices", "react patterns", "tsx best practices",
            "component structure", "react performance",
        ],
        "description": "Reading/writing React components with best practices",
    },
    {
        "name": "ui-design-system",
        "keywords": [
            "shadcn", "radix", "tailwindcss", "component library",
            "accessible components", "dark mode", "design tokens",
        ],
        "description": "React UI component systems — TailwindCSS + Radix + shadcn/ui",
    },
    {
        "name": "web-design-guidelines",
        "keywords": [
            "web guidelines", "wcag", "aria", "contrast", "responsive check",
            "web interface guidelines", "check accessibility",
        ],
        "description": "Review UI against web interface guidelines — accessibility, responsive, UX best practices",
    },
    {
        "name": "web-design-reviewer",
        "keywords": [
            "review website", "check the ui", "fix the layout",
            "find design problems", "visual inspection", "layout breakage",
        ],
        "description": "Visually inspect sites to find and fix design issues at the source code level",
    },
    # ── Copy & content for sites ─────────────────────────────────────
    {
        "name": "landing-page-copywriter",
        "keywords": [
            "headline", "hero copy", "cta", "value proposition",
            "landing copy", "sales page", "conversion copy",
            "page sections", "website copy",
        ],
        "description": "High-converting landing page copy — headlines, value props, CTAs, section copy",
    },
    # ── Domain & deploy ──────────────────────────────────────────────
    {
        "name": "domain-name-brainstormer",
        "keywords": [
            "domain", "domain name", "tld", ".com", ".io", ".dev", ".ai",
            "domain ideas", "url", "website address",
        ],
        "description": "Generate creative domain name ideas and check availability across TLDs",
    },
    # ── Testing ──────────────────────────────────────────────────────
    {
        "name": "webapp-testing",
        "keywords": [
            "test website", "verify page", "browser test", "playwright",
            "local app test", "capture screenshot", "debug ui",
        ],
        "description": "Interact with and test web apps via Playwright — verify frontend, capture screenshots, debug",
    },
]


def _load_skill_content(skill_name: str) -> str | None:
    """Read SKILL.md from Jcode or agents skill directories."""
    for base in (JCODE_SKILLS_DIR, AGENTS_SKILLS_DIR):
        skill_path = base / skill_name / "SKILL.md"
        if skill_path.is_file():
            try:
                return skill_path.read_text(encoding="utf-8")
            except Exception as e:
                logger.error("Error reading skill %s: %s", skill_name, e)
                return None
    logger.warning("Skill not found: %s", skill_name)
    return None


def detect_skills(message: str, max_skills: int = 2) -> list[dict]:
    """Detect relevant Website skills from a message.

    Returns a list of matched skills with their loaded content.
    At most `max_skills` skills are returned.
    """
    msg_lower = message.lower()
    matched: list[dict] = []

    for skill in WEBSITE_SKILL_REGISTRY:
        for kw in skill["keywords"]:
            if kw in msg_lower:
                content = _load_skill_content(skill["name"])
                if content:
                    matched.append({
                        "name": skill["name"],
                        "description": skill["description"],
                        "content": content,
                    })
                break  # One match per skill
        if len(matched) >= max_skills:
            break

    return matched


MAX_SKILL_CONTENT_CHARS = 2000  # Per skill — keeps total under LLM token caps
MAX_TOTAL_SKILL_CHARS = 4000    # Total skill context cap


def build_skill_context(skills: list[dict]) -> str:
    """Build a skill context block from matched skills.

    Truncates each skill's content to MAX_SKILL_CONTENT_CHARS to keep the
    total context bounded.
    """
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
        "── RELEVANT SKILLS ────────────────────────\n"
        "Tuze jo skills relevant lagti hain, unko use kar:\n\n"
        + "\n\n".join(blocks)
        + "\n──────────────────────────────────────────"
    )


def list_website_skills() -> list[dict]:
    """List all Website-relevant skills (without loading content)."""
    return [
        {"name": s["name"], "description": s["description"], "keywords": s["keywords"]}
        for s in WEBSITE_SKILL_REGISTRY
    ]
