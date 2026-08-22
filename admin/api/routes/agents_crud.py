"""CRUD for user-added (dynamic) agents.

Complements agent_aliases.py (which serves built-in worker agents). This
router exposes the dynamic agent registry (admin/agency/agent_registry.py)
so the frontend can list / create / get / delete / chat-with custom agents.

All persistence lives in agent_registry; this module is a thin HTTP layer.
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from admin.agency import agent_registry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agents/custom", tags=["agents-custom"])


class AgentCreate(BaseModel):
    name: str
    role: str
    system_prompt: str = ""
    model: str = ""
    api_key_ref: str = ""
    tools: list[str] = []


class AgentChat(BaseModel):
    message: str


@router.get("")
async def list_custom_agents() -> dict[str, Any]:
    """List all user-added agents from the registry."""
    agents = await agent_registry.list_agents()
    return {"status": "ok", "agents": agents}


@router.post("")
async def create_custom_agent(body: AgentCreate) -> dict[str, Any]:
    """Create a new custom agent."""
    if not (body.name or "").strip() or not (body.role or "").strip():
        raise HTTPException(400, "name and role are required")
    agent = await agent_registry.create_agent(
        name=body.name.strip(),
        role=body.role.strip(),
        system_prompt=body.system_prompt,
        model=body.model,
        api_key_ref=body.api_key_ref,
        tools=body.tools,
    )
    return {"status": "ok", "agent": agent}


@router.get("/{agent_id}")
async def get_custom_agent(agent_id: str) -> dict[str, Any]:
    """Fetch a single custom agent by id."""
    agent = await agent_registry.get_agent(agent_id)
    if agent is None:
        raise HTTPException(404, f"Agent not found: {agent_id}")
    return {"status": "ok", "agent": agent}


@router.delete("/{agent_id}")
async def delete_custom_agent(agent_id: str) -> dict[str, Any]:
    """Delete a custom agent."""
    deleted = await agent_registry.delete_agent(agent_id)
    if not deleted:
        raise HTTPException(404, f"Agent not found: {agent_id}")
    return {"status": "ok", "deleted": True}


@router.post("/{agent_id}/chat")
async def chat_custom_agent(agent_id: str, body: AgentChat) -> dict[str, Any]:
    """Chat with a custom agent (routed through the worker bridge)."""
    from admin.agency.workers import run_worker

    message = (body.message or "").strip()
    if not message:
        raise HTTPException(400, "message is required")

    result = await run_worker(
        agent_id,
        message,
        {"scope": {"kind": "agency", "workspace_id": "agency"}},
    )
    return {"status": "ok", "result": result}
