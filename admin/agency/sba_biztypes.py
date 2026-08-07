# admin/agency/sba_biztypes.py
"""Per-workspace decision support for the SBA lead-gen autopilot.

The autopilot needs to know, for each workspace, whether the client business
actually needs SBA-style local cold-email lead generation, and - when it does -
what to work on: a niche rotation, an outreach angle, and where to keep the
strategy / reasoning-journal / rotation-state files.

This module is deliberately dumb and synchronous: it classifies businesses from
keywords (D2C/ecommerce/etc. sell direct and get ``needs_sba False``; local
services get ``True``; unknown stays ``False`` so the owner can enable manually)
and merges the classification with persisted overrides from a per-workspace
config file. It never raises and never makes network calls, so the autopilot can
call it unconditionally on every pass.
"""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

logger = logging.getLogger("sba.biztypes")

# Persisted per-workspace config; overridable for tests / other hosts.
CONFIG_FILE = os.environ.get(
    "SBA_WORKSPACES_CONFIG_FILE",
    "/home/ubuntu/sba-backend/sba_workspaces.json",
)

# Keys callers may persist per workspace.
PERSISTED_KEYS = ("enabled", "owner_email", "industry", "category", "rotation", "angle")

# Businesses that sell direct (D2C / ecommerce / product / software): no local
# cold-email lead generation needed.
DIRECT_SALE_KEYWORDS = (
    "d2c", "ecommerce", "e-commerce", "e commerce", "retail", "saas", "software",
    "app", "fashion", "apparel", "store", "restaurant", "cafe", "food",
    "beverage", "cosmetics", "beauty brand",
)

# Local-services businesses: exactly the niche cold-email lead gen targets.
LOCAL_SERVICES_KEYWORDS = (
    "real estate", "realtor", "property", "plumbing", "plumber", "hvac",
    "heating", "air conditioning", "electrical", "electrician", "roofing",
    "roofer", "landscaping", "lawn", "pest control", "cleaning", "construction",
    "contractor", "painting", "painter", "auto repair", "garage", "mechanic",
    "salon", "spa", "barber", "dentist", "clinic", "law", "legal", "accounting",
    "tax", "marketing agency", "staffing", "it services", "commercial cleaning",
)

AGENCY_ANGLE = (
    "Help local businesses get more customers with a professional website and local SEO"
)

# Default niche rotation for the agency workspace (38 targets).
DEFAULT_ROTATION: list[tuple[str, str, str]] = [
    ("plumber", "Houston", "TX"), ("electrician", "San Antonio", "TX"),
    ("hvac", "Austin", "TX"), ("roofer", "Dallas", "TX"),
    ("landscaper", "Fort Worth", "TX"), ("auto repair", "Houston", "TX"),
    ("cleaning service", "San Antonio", "TX"), ("handyman", "Austin", "TX"),
    ("painter", "Dallas", "TX"), ("dentist", "Fort Worth", "TX"),
    ("plumber", "Austin", "TX"), ("electrician", "Houston", "TX"),
    ("hvac", "Dallas", "TX"), ("roofer", "San Antonio", "TX"),
    ("landscaper", "Houston", "TX"), ("auto repair", "Austin", "TX"),
    ("cleaning service", "Dallas", "TX"), ("handyman", "Fort Worth", "TX"),
    ("painter", "San Antonio", "TX"), ("salon", "Houston", "TX"),
    ("plumber", "Phoenix", "AZ"), ("electrician", "Atlanta", "GA"),
    ("hvac", "Charlotte", "NC"), ("roofer", "Tampa", "FL"),
    ("landscaper", "Orlando", "FL"), ("auto repair", "Denver", "CO"),
    ("cleaning service", "Las Vegas", "NV"), ("handyman", "Nashville", "TN"),
    ("painter", "Oklahoma City", "OK"), ("salon", "Memphis", "TN"),
    ("plumber", "San Diego", "CA"), ("electrician", "Columbus", "OH"),
    ("hvac", "Kansas City", "MO"), ("roofer", "New Orleans", "LA"),
    ("landscaper", "Louisville", "KY"), ("auto repair", "Albuquerque", "NM"),
    ("cleaning service", "Tulsa", "OK"), ("handyman", "El Paso", "TX"),
]

# A few tailored rotations for common categories; everything else falls back to
# the generic Texas rotation.
TAILORED_ROTATIONS: dict[str, list[tuple[str, str, str]]] = {
    "real estate": [
        ("real estate agent", "Houston", "TX"),
        ("realtor", "Dallas", "TX"),
        ("property management", "Austin", "TX"),
    ],
    "plumbing": [
        ("plumber", "Houston", "TX"),
        ("plumber", "Austin", "TX"),
        ("plumber", "Dallas", "TX"),
    ],
}

TAILORED_ANGLES: dict[str, str] = {
    "real estate": (
        "Help local property owners and real estate businesses get more clients "
        "with a strong online presence"
    ),
}


# ── Classification ───────────────────────────────────────────────────────────


def _matches(haystack: str, keywords: tuple[str, ...]) -> str | None:
    """Return the first keyword found in the lowercased haystack, else None."""
    lowered = haystack.lower()
    for kw in keywords:
        if kw in lowered:
            return kw
    return None


def classify_business(
    workspace_name: str,
    industry: str = "",
    description: str = "",
    category: str = "",
) -> dict[str, Any]:
    """Decide whether a workspace's client business needs SBA lead generation.

    Returns ``{"needs_sba": bool, "category": str, "rotation": [...], "angle": str}``.
    The agency workspace is always enabled (it *is* the lead-gen business).
    Businesses that sell direct (D2C / ecommerce / software / etc.) are never
    SBA candidates. Local-services keywords enable it. Unknown stays disabled
    (conservative: the owner enables manually).
    """
    if workspace_name.strip().lower() == "agency":
        return {
            "needs_sba": True,
            "category": "local business",
            "rotation": [list(t) for t in DEFAULT_ROTATION],
            "angle": AGENCY_ANGLE,
        }

    haystack = " ".join([industry, description, category, workspace_name])
    if _matches(haystack, DIRECT_SALE_KEYWORDS):
        return {
            "needs_sba": False,
            "category": _matches(haystack, DIRECT_SALE_KEYWORDS) or "",
            "rotation": [],
            "angle": "",
        }

    matched = _matches(haystack, LOCAL_SERVICES_KEYWORDS)
    if not matched:
        return {"needs_sba": False, "category": "", "rotation": [], "angle": ""}

    rotation = TAILORED_ROTATIONS.get(
        matched,
        [[matched, "Houston", "TX"], [matched, "Dallas", "TX"], [matched, "Austin", "TX"]],
    )
    angle = TAILORED_ANGLES.get(
        matched, f"Help {matched} businesses get more local customers"
    )
    return {
        "needs_sba": True,
        "category": matched,
        "rotation": [list(t) for t in rotation],
        "angle": angle,
    }


# ── Persistence ──────────────────────────────────────────────────────────────


def _load_all() -> dict[str, Any]:
    """Read the whole config file as a dict; never raise."""
    try:
        with open(CONFIG_FILE, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
        logger.warning("sba workspaces config is not a dict: %r", type(data))
    except FileNotFoundError:
        pass
    except Exception as exc:  # noqa: BLE001 - never raise
        logger.warning("could not read sba workspaces config %s: %s", CONFIG_FILE, exc)
    return {}


def _save_all(data: dict[str, Any]) -> bool:
    """Atomically persist the config file; never raise."""
    try:
        tmp = CONFIG_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        os.replace(tmp, CONFIG_FILE)
        return True
    except Exception as exc:  # noqa: BLE001 - never raise
        logger.warning("could not write sba workspaces config %s: %s", CONFIG_FILE, exc)
        return False


def get_workspace_config(workspace_name: str) -> dict[str, Any]:
    """Merged per-workspace config: persisted overrides beat classification.

    Always includes ``name`` and ``needs_sba`` (== ``enabled``). Persisted keys:
    ``enabled`` (default = classified ``needs_sba``), ``owner_email`` (default ""),
    ``industry``, ``category``, ``rotation``, ``angle``.
    """
    name = workspace_name.strip()
    base = classify_business(name)
    persisted = (_load_all() or {}).get(name, {})

    enabled = persisted.get("enabled", base["needs_sba"])
    category = persisted.get("category", base["category"])
    rotation = persisted.get("rotation", base["rotation"])
    angle = persisted.get("angle", base["angle"])

    return {
        "name": name,
        "needs_sba": bool(enabled),
        "enabled": bool(enabled),
        "owner_email": str(persisted.get("owner_email", "")),
        "industry": str(persisted.get("industry", "")),
        "category": str(category),
        "rotation": rotation,
        "angle": str(angle),
    }


def set_workspace_config(workspace_name: str, **updates: Any) -> bool:
    """Persist overrides for one workspace (create the entry if missing).

    Allowed keys: ``enabled``, ``owner_email``, ``industry``, ``category``,
    ``rotation``, ``angle``. Returns True on a successful write.
    """
    name = workspace_name.strip()
    if not name:
        return False
    data = _load_all()
    entry = data.get(name)
    if not isinstance(entry, dict):
        entry = {}
    changed = False
    for key, value in updates.items():
        if key in PERSISTED_KEYS:
            entry[key] = value
            changed = True
    if not changed:
        return False
    data[name] = entry
    return _save_all(data)


def list_sba_workspaces() -> list[dict[str, Any]]:
    """Every workspace with ``enabled`` True.

    Each entry: ``{"name", "category", "owner_email", "rotation", "angle"}``.
    If the agency workspace is missing from the config, it is included enabled
    with the default category / rotation / angle. Never raises.
    """
    try:
        data = _load_all()
        if "agency" not in data:
            data["agency"] = {
                "enabled": True,
                "category": "local business",
                "rotation": [list(t) for t in DEFAULT_ROTATION],
                "angle": AGENCY_ANGLE,
            }
        out: list[dict[str, Any]] = []
        for name, entry in data.items():
            if not isinstance(entry, dict):
                continue
            if not entry.get("enabled", False):
                continue
            out.append(
                {
                    "name": str(name),
                    "category": str(entry.get("category", "")),
                    "owner_email": str(entry.get("owner_email", "")),
                    "rotation": entry.get("rotation", []),
                    "angle": str(entry.get("angle", "")),
                }
            )
        return out
    except Exception as exc:  # noqa: BLE001 - never raise
        logger.warning("list_sba_workspaces failed: %s", exc)
        return []


# ── Paths ────────────────────────────────────────────────────────────────────


def _sanitize(workspace_name: str) -> str:
    return re.sub(r"[^a-z0-9_]", "_", workspace_name.strip().lower()) or "workspace"


def strategy_path(workspace_name: str) -> str:
    """Strategy-file path for a workspace (name sanitized)."""
    return f"/home/ubuntu/sba-backend/sba_strategy_{_sanitize(workspace_name)}.json"


def journal_path(workspace_name: str) -> str:
    """Reasoning-journal path for a workspace (name sanitized)."""
    return f"/home/ubuntu/sba-backend/sba_reasoning_{_sanitize(workspace_name)}.log"


def rotation_state_path(workspace_name: str) -> str:
    """Rotation-state path for a workspace (name sanitized)."""
    return f"/home/ubuntu/sba-backend/sba_rotation_{_sanitize(workspace_name)}.state"
