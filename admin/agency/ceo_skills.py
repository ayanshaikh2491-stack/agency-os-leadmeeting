"""CEO Agent Skills — the CEO's OWN reasoning + reporting skills.

Unlike the worker agents (sba/seo/social/website) which pull DOMAIN skills from the
Jcode catalog, the CEO's skills are its OWN brain: how it thinks like a real CEO
(strategic decision-making) and how it reports work back to the boss (a CEO-style
status report, not a raw data dump).

These are discovered locally from this folder (not from ~/.jcode/skills) because
they belong to the CEO's role, not to a domain agent. The pattern mirrors the
other agents' `*_skills.py` (detect by keyword, build a context block) so it slots
into the same mechanism.

Skills shipped here (found via find-skills tooling):
  - ceo-skill        : world-class Chief-of-Staff decision advisor (strategy,
                       risk, bias-check, war-gaming, stakeholder mapping).
  - status-report     : CEO work-report voice (digest + detailed, Hinglish,
                       🟢🟡🔴 health, actionable next-steps).
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# ── CEO skills live in this folder (CEO's own role skills) ───────────────────
CEO_SKILLS_DIR = Path(__file__).parent / "ceo_skills_repo"

# ── CEO skill registry (its own brain) ──────────────────────────────────────
# Each skill is a folder under CEO_SKILLS_DIR with a SKILL.md.
CEO_SKILL_REGISTRY: list[dict] = [
    {
        "name": "ceo-skill",
        "keywords": [
            "decision", "strategy", "strategic", "should we", "trade-off",
            "risk", "stakeholder", "board", "investor", "prioritize",
            "priority", "resource", "allocation", "okr", "kpi", "crisis",
            "war game", "red team", "blind spot", "bias", "business call",
            "competitive", "soch", "plan", "evaluate", "which agent",
            "delegate who", "what to do",
        ],
        "description": "Real-CEO strategic decision advisor: framing, risk, bias-check, war-gaming, stakeholder mapping",
    },
    {
        "name": "status-report",
        "keywords": [
            "report", "status", "update", "digest", "summary", "kya hua",
            "kya chal raha", "progress", "health", "weekly", "monthly",
            "tell me", "inform", "brief me", "what happened", "results",
        ],
        "description": "CEO work-report voice: candid Hinglish digest + detailed, 🟢🟡🔴 health, actionable next-steps",
    },
]

MAX_SKILL_CONTENT_CHARS = 6000   # CEO model context is larger; keep generous
MAX_TOTAL_SKILL_CHARS = 12000


def _load_skill_content(skill_name: str) -> str | None:
    """Read SKILL.md from the CEO skills folder."""
    skill_path = CEO_SKILLS_DIR / skill_name / "SKILL.md"
    if not skill_path.is_file():
        logger.warning("CEO skill not found: %s (%s)", skill_name, skill_path)
        return None
    try:
        return skill_path.read_text(encoding="utf-8")
    except Exception as e:  # noqa: BLE001
        logger.error("Error reading CEO skill %s: %s", skill_name, e)
        return None


def detect_ceo_skills(message: str, max_skills: int = 2) -> list[dict]:
    """Detect relevant CEO skills from the boss's message.

    Returns matched skills with loaded content. At most `max_skills` returned.
    """
    msg_lower = message.lower()
    matched: list[dict] = []

    for skill in CEO_SKILL_REGISTRY:
        for kw in skill["keywords"]:
            if kw in msg_lower:
                content = _load_skill_content(skill["name"])
                if content:
                    matched.append({
                        "name": skill["name"],
                        "description": skill["description"],
                        "content": content,
                    })
                break
        if len(matched) >= max_skills:
            break

    return matched


def build_ceo_skill_context(skills: list[dict]) -> str:
    """Build the CEO skill context block from matched skills."""
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
            f"### CEO Skill: {s['name']}\n"
            f"{s['description']}\n\n"
            f"{content}"
        )

    if not blocks:
        return ""

    return (
        "── YOUR CEO SKILLS (use these to think & report like a real CEO) ──\n"
        "Tu ek asli CEO hai. In skills ko apne tools/functions ke saath use kar:\n\n"
        + "\n\n".join(blocks)
        + "\n──────────────────────────────────────────"
    )


def list_ceo_skills() -> list[dict]:
    """List the CEO's own skills (without loading content)."""
    return [
        {"name": s["name"], "description": s["description"], "keywords": s["keywords"]}
        for s in CEO_SKILL_REGISTRY
    ]
