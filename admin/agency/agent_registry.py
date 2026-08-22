"""Dynamic Agent Registry — Munder-style user-added agents.

Built-in employees (sba, seo, website, content, ads, social, analytics) are
registered in workers.register_builtins(). This module adds PERSISTENT,
user-created agents on top of them: a user can add/remove agents at runtime
(name, role, system prompt, model, api-key ref, tools) and the CEO + workers
layer picks them up automatically.

Storage: the same workspace SQLite DB used by mandates.py, so no new infra.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

import aiosqlite

from admin.persistence import get_workspace_db, row_to_dict

CREATE_CUSTOM_AGENTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS custom_agents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    system_prompt TEXT NOT NULL DEFAULT '',
    model TEXT NOT NULL DEFAULT '',
    api_key_ref TEXT NOT NULL DEFAULT '',
    tools TEXT NOT NULL DEFAULT '[]',
    created_by TEXT NOT NULL DEFAULT 'owner',
    created_at TEXT NOT NULL
)
"""

_ensured: bool = False


async def _ensure_table() -> None:
    global _ensured
    if _ensured:
        return
    db = await get_workspace_db()
    await db.execute(CREATE_CUSTOM_AGENTS_TABLE_SQL)
    await db.commit()
    _ensured = True


def _new_id() -> str:
    return "agent_" + uuid.uuid4().hex[:12]


async def create_agent(
    name: str,
    role: str,
    system_prompt: str = "",
    model: str = "",
    api_key_ref: str = "",
    tools: list[str] | None = None,
    created_by: str = "owner",
) -> dict[str, Any]:
    """Add a new custom agent. Returns the stored record (with id)."""
    name = (name or "").strip()
    role = (role or "").strip()
    if not name or not role:
        raise ValueError("name and role are required")
    await _ensure_table()
    agent_id = _new_id()
    created_at = datetime.now(timezone.utc).isoformat()
    db = await get_workspace_db()
    await db.execute(
        """
        INSERT INTO custom_agents
            (id, name, role, system_prompt, model, api_key_ref, tools, created_by, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            agent_id, name, role, system_prompt, model, api_key_ref,
            json.dumps(tools or []), created_by, created_at,
        ),
    )
    await db.commit()
    return await get_agent(agent_id)  # type: ignore[return-value]


async def get_agent(agent_id: str) -> dict[str, Any] | None:
    await _ensure_table()
    db = await get_workspace_db()
    async with db.execute(
        "SELECT * FROM custom_agents WHERE id = ?", (agent_id,)
    ) as cursor:
        row = await cursor.fetchone()
    return _deserialize(row) if row else None


async def list_agents() -> list[dict[str, Any]]:
    await _ensure_table()
    db = await get_workspace_db()
    async with db.execute("SELECT * FROM custom_agents ORDER BY created_at") as cursor:
        rows = await cursor.fetchall()
    return [_deserialize(row) for row in rows]


async def delete_agent(agent_id: str) -> bool:
    await _ensure_table()
    db = await get_workspace_db()
    result = await db.execute("DELETE FROM custom_agents WHERE id = ?", (agent_id,))
    await db.commit()
    return result.rowcount > 0


def _deserialize(row: aiosqlite.Row) -> dict[str, Any]:
    data = row_to_dict(row)
    try:
        data["tools"] = json.loads(data.get("tools") or "[]")
    except (ValueError, TypeError):
        data["tools"] = []
    return data
