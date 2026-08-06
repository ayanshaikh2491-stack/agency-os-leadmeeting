"""Per-workspace organic post history (append-only JSONL log).

Every organic post — manual or scheduled — is recorded here so the frontend
can show a real proof-of-work timeline and stats instead of sample data.

Files live in admin/organic_data/<workspace_id>/history.jsonl
Override the root with the ORGANIC_DATA_DIR env var (used by tests).
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

ORGANIC_DATA_DIR = Path(
    os.environ.get("ORGANIC_DATA_DIR", str(Path(__file__).resolve().parent.parent.parent / "organic_data"))
)

# Sensitive payload keys that must never be persisted to history.
_SENSITIVE_KEYS = {"password", "client_secret", "access_token", "bot_token", "token", "secret"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _history_file(workspace_id: str) -> Path:
    d = ORGANIC_DATA_DIR / workspace_id
    d.mkdir(parents=True, exist_ok=True)
    return d / "history.jsonl"


def _sanitize_payload(payload: dict | None) -> dict:
    out: dict = {}
    for k, v in (payload or {}).items():
        if k.lower() in _SENSITIVE_KEYS:
            continue
        if isinstance(v, (str, int, float, bool)) or v is None:
            out[k] = v
        elif isinstance(v, list):
            out[k] = [str(x) for x in v[:20]]
        else:
            out[k] = str(v)[:500]
    return out


def record_post(
    workspace_id: str,
    channel: str,
    result: dict[str, Any],
    payload: dict | None = None,
    scheduled_for: str | None = None,
) -> str:
    """Append one post event to the workspace history log. Returns history_id.

    Fail-open: a disk error must never break posting, so this logs and returns
    a synthetic id instead of raising.
    """
    entry = {
        "id": uuid.uuid4().hex[:12],
        "ts": _now(),
        "channel": channel,
        "status": result.get("status", "unknown"),
        "post_id": result.get("post_id", ""),
        "post_url": result.get("post_url", ""),
        "error": result.get("error", "")[:500],
        "scheduled_for": scheduled_for or "",
        "payload": _sanitize_payload(payload),
    }
    try:
        with open(_history_file(workspace_id), "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError as exc:
        logger.warning("history write failed for %s/%s: %s", workspace_id, channel, exc)
    return entry["id"]


def list_posts(workspace_id: str, channel: str | None = None, limit: int = 200) -> list[dict]:
    """Return post history, newest first. Optionally filter by channel."""
    f = _history_file(workspace_id)
    if not f.exists():
        return []
    entries: list[dict] = []
    try:
        with open(f, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        return []
    if channel:
        entries = [e for e in entries if e.get("channel") == channel]
    entries.sort(key=lambda e: e.get("ts", ""), reverse=True)
    return entries[: max(1, limit)]


def history_stats(workspace_id: str) -> dict[str, Any]:
    """Per-channel / per-status counts plus totals for the workspace."""
    entries = list_posts(workspace_id, limit=10000)
    by_channel: dict[str, int] = {}
    by_status: dict[str, int] = {}
    published = 0
    for e in entries:
        ch = e.get("channel", "?")
        st = e.get("status", "?")
        by_channel[ch] = by_channel.get(ch, 0) + 1
        by_status[st] = by_status.get(st, 0) + 1
        if st == "published":
            published += 1
    return {
        "total": len(entries),
        "published": published,
        "by_channel": by_channel,
        "by_status": by_status,
    }
