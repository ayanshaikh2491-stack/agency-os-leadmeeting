"""SBA Agent Skills — loaded from Jcode's skill catalog.

Each skill is a SKILL.md file in ~/.jcode/skills/<skill-name>/.
Relevant skills are auto-detected from the message and passed as context.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Path to Jcode skills ────────────────────────────────────────────
JCODE_SKILLS_DIR = Path.home() / ".jcode" / "skills"

# ── SBA-relevant skills (sales agent role only) ──────────────────────────
SBA_SKILL_REGISTRY: list[dict] = [
    {
        "name": "cold-outreach",
        "keywords": [
            "cold outreach", "cold dm", "cold email", "prospect", "linkedin message",
            "cold message", "outbound", "lead generation", "dm", "direct message",
            "follow up", "follow-up", "sequence", "reply", "open rate",
        ],
        "description": "8 proven sales systems for cold outreach, DM, email prospecting",
    },
    {
        "name": "alex-hormozi-pitch",
        "keywords": [
            "offer", "pitch", "value proposition", "pricing", "guarantee",
            "grand slam", "irresistible offer", "value stack", "bonus",
            "scarcity", "urgency",
        ],
        "description": "Create irresistible offers using Alex Hormozi methodology",
    },
    {
        "name": "sales-enablement",
        "keywords": [
            "sales deck", "pitch deck", "one pager", "one-pager", "objection",
            "demo script", "proposal", "sales playbook", "buyer persona",
            "sales collateral", "talk track", "roi calculator", "case study brief",
        ],
        "description": "Sales collateral, pitch decks, objection handling, proposal templates",
    },
    {
        "name": "lead-qualification",
        "keywords": [
            "qualify", "qualification", "lead score", "bant", "champ",
            "meddic", "score", "red flag", "dq", "lead evaluation",
            "qualify lead", "prospect qualify", "is this lead good",
        ],
        "description": "CHAMP/BANT/MEDDIC lead qualification framework with scoring",
    },
    {
        "name": "meeting-companion",
        "keywords": [
            "meeting", "schedule", "call", "discovery", "demo",
            "follow up", "post-meeting", "pre-meeting", "meeting script",
            "handoff", "objection handling", "close", "next step",
        ],
        "description": "Full meeting lifecycle — scheduling, live companion, follow-up, handoff",
    },
]


def _load_skill_content(skill_name: str) -> str | None:
    """Read SKILL.md from Jcode skills directory."""
    skill_path = JCODE_SKILLS_DIR / skill_name / "SKILL.md"
    if not skill_path.is_file():
        logger.warning("Skill not found: %s (%s)", skill_name, skill_path)
        return None
    try:
        return skill_path.read_text(encoding="utf-8")
    except Exception as e:
        logger.error("Error reading skill %s: %s", skill_name, e)
        return None


def detect_skills(message: str, max_skills: int = 2) -> list[dict]:
    """Detect relevant SBA skills from a message.

    Returns a list of matched skills with their loaded content.
    At most `max_skills` skills are returned.
    """
    msg_lower = message.lower()
    matched: list[dict] = []

    for skill in SBA_SKILL_REGISTRY:
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


MAX_SKILL_CONTENT_CHARS = 2000  # Per skill — keeps total under Groq free TPM
MAX_TOTAL_SKILL_CHARS = 4000   # Total skill context cap


def build_skill_context(skills: list[dict]) -> str:
    """Build a skill context block from matched skills.

    Truncates each skill's content to MAX_SKILL_CONTENT_CHARS to stay
    within Groq free-tier TPM limits (total context < 4000 chars).
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


def list_sba_skills() -> list[dict]:
    """List all SBA-relevant skills (without loading content)."""
    return [
        {"name": s["name"], "description": s["description"], "keywords": s["keywords"]}
        for s in SBA_SKILL_REGISTRY
    ]
