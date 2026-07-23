"""Workspace manager — CRUD + agent output tracking, reviews, error routing.

Currently uses an in-memory store. Will be backed by PostgreSQL.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from admin.api.models.schemas import WorkspaceCreate, WorkspaceOut

import logging
logger = logging.getLogger(__name__)

# ── In-memory store (swap with DB later) ───────────────────────────────────
_workspaces: dict[str, dict[str, Any]] = {}
_agent_outputs: list[dict[str, Any]] = []     # CEO tracks agent work for review
_pending_reviews: list[dict[str, Any]] = []   # Outputs awaiting CEO review
_completed_reviews: list[dict[str, Any]] = [] # CEO review verdicts
_error_logs: list[dict[str, Any]] = []        # Error routing history

# Default agent types every workspace gets
DEFAULT_AGENTS = ["sba", "seo", "content", "website", "ads", "social", "analytics", "memory"]


def _build_knowledge_context(knowledge: dict) -> str:
    """Build a human-readable knowledge context string for Content Agent.
    
    Injected into Content Agent's message so it benefits from cross-project
    learnings when starting work on a new workspace.
    """
    parts = ["\n## AGENCY CROSS-PROJECT KNOWLEDGE (from previous projects)"]
    
    patterns = knowledge.get("prompt_patterns", [])
    if patterns:
        parts.append("\n### Prompt Patterns That Work")
        for p in patterns[:5]:
            parts.append(
                f"- [{p.get('visual_type', '?')}/{p.get('platform', '?')}] "
                f"\"{p.get('prompt_template', '')[:120]}\" "
                f"(used {p.get('success_count', 0)} times)"
            )
    
    insights = knowledge.get("brand_insights", [])
    if insights:
        parts.append("\n### Brand/Visual Insights")
        for i in insights[:5]:
            parts.append(f"- {i.get('type', '?')}: {i.get('insight', '')}")
    
    tips = knowledge.get("platform_tips", [])
    if tips:
        parts.append("\n### Platform Tips")
        for t in tips[:3]:
            parts.append(
                f"- {t.get('total_jobs', 0)} jobs done, "
                f"avg {t.get('avg_gpu_minutes', 0):.1f} min GPU per job"
            )
    
    if len(parts) == 1:
        return ""  # No knowledge to inject
    
    parts.append("\nUse these learnings when enhancing briefs and creating prompts.")
    return "\n".join(parts)


# ── Workspace CRUD ───────────────────────────────────────────────────────────

def create_workspace(payload: WorkspaceCreate) -> WorkspaceOut:
    wid = uuid.uuid4().hex[:12]
    now = datetime.now(timezone.utc)
    record: dict[str, Any] = {
        "id": wid,
        "name": payload.name,
        "client_name": payload.client_name or payload.name,
        "description": payload.description or "",
        "created_at": now,
        "agents": list(DEFAULT_AGENTS),
        "client_context": payload.client_context.model_dump() if payload.client_context else None,
    }
    _workspaces[wid] = record

    # Create per-workspace Content Agent memory
    try:
        from admin.workspace.content_store import get_content_store
        store = get_content_store()
        client_ctx = payload.client_context.model_dump() if payload.client_context else {}
        store.get_or_create(
            workspace_id=wid,
            workspace_name=payload.name,
            client_name=payload.client_name or payload.name,
            industry=client_ctx.get("industry", ""),
        )
        logger.info("Created Content Agent memory for workspace '%s'", payload.name)
    except Exception as e:
        logger.warning("Failed to create Content Agent memory: %s", e)

    return WorkspaceOut(**record)


def get_workspace(wid: str) -> WorkspaceOut | None:
    record = _workspaces.get(wid)
    return WorkspaceOut(**record) if record else None


def list_workspaces() -> list[WorkspaceOut]:
    return [WorkspaceOut(**r) for r in _workspaces.values()]


def delete_workspace(wid: str) -> bool:
    return _workspaces.pop(wid, None) is not None


# ── Agent Output Tracking ────────────────────────────────────────────────────

def store_agent_output(
    workspace_id: str,
    agent_type: str,
    task: str,
    output: str,
) -> dict[str, Any]:
    """Store agent output for CEO review (Q20)."""
    record = {
        "id": f"out_{uuid.uuid4().hex[:8]}",
        "workspace_id": workspace_id,
        "agent_type": agent_type,
        "task": task,
        "output": output,
        "output_preview": output[:300],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "reviewed": False,
    }
    _agent_outputs.append(record)
    _pending_reviews.append(record)
    return record


def list_pending_reviews() -> list[dict[str, Any]]:
    """List agent outputs pending CEO review."""
    return [r for r in _pending_reviews if not r.get("reviewed")]


# ── Review Storage ───────────────────────────────────────────────────────────

def store_review(
    workspace_id: str,
    agent_type: str,
    output_id: str,
    verdict: str,
    feedback: str = "",
) -> dict[str, Any]:
    """Store CEO review verdict (Q20)."""
    record = {
        "id": f"rev_{uuid.uuid4().hex[:8]}",
        "workspace_id": workspace_id,
        "agent_type": agent_type,
        "output_id": output_id,
        "verdict": verdict,
        "feedback": feedback,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _completed_reviews.append(record)

    # Mark output as reviewed
    for r in _pending_reviews:
        if r.get("id") == output_id:
            r["reviewed"] = True
            break

    return record


def list_reviews(workspace_id: str | None = None) -> list[dict[str, Any]]:
    """List completed reviews."""
    reviews = _completed_reviews
    if workspace_id:
        reviews = [r for r in reviews if r["workspace_id"] == workspace_id]
    return reviews


# ── Error Log ────────────────────────────────────────────────────────────────

def store_error(
    workspace_id: str,
    error_type: str,
    severity: str,
    description: str,
    routed_to: str = "",
) -> dict[str, Any]:
    """Log error routing (Q21)."""
    record = {
        "id": f"err_{uuid.uuid4().hex[:8]}",
        "workspace_id": workspace_id,
        "error_type": error_type,
        "severity": severity,
        "description": description,
        "routed_to": routed_to,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "resolved": False,
    }
    _error_logs.append(record)
    return record


def list_errors(workspace_id: str | None = None, unresolved_only: bool = False) -> list[dict[str, Any]]:
    """List error logs."""
    errors = _error_logs
    if workspace_id:
        errors = [e for e in errors if e["workspace_id"] == workspace_id]
    if unresolved_only:
        errors = [e for e in errors if not e.get("resolved")]
    return errors


# ── Agent Routing ────────────────────────────────────────────────────────────

async def route_to_agent(
    workspace_id: str,
    agent_type: str,
    message: str,
) -> str:
    """Route a message to a specific agent inside a workspace.

    Used by CEO for delegation. Returns the agent's response text.
    """
    ws = get_workspace(workspace_id)
    if not ws:
        return f"Workspace '{workspace_id}' not found."
    if agent_type not in ws.agents:
        return f"Agent '{agent_type}' not in workspace. Available: {ws.agents}"

    # SBA has its own agent class
    if agent_type == "sba":
        from admin.agency.sba import SBAAgent
        agent = SBAAgent(workspace_name=ws.name, client_name=ws.client_name)
        response, _ = await agent.chat(message)
        return response

    # Domain-specific workspace agents (LangGraph-powered)
    _domain_agents = {
        "seo": ("admin.workspace.agents.seo", "SEOAgent"),
        "ads": ("admin.workspace.agents.ads", "AdsAgent"),
        "website": ("admin.workspace.agents.website", "WebsiteAgent"),
        "social": ("admin.workspace.agents.social", "SocialAgent"),
        "content": ("admin.workspace.agents.content", "ContentAgent"),
        "analytics": ("admin.workspace.agents.analytics", "AnalyticsAgent"),
    }

    if agent_type in _domain_agents:
        module_path, class_name = _domain_agents[agent_type]
        try:
            import importlib
            module = importlib.import_module(module_path)
            agent_class = getattr(module, class_name)
            
            # Build agent kwargs
            agent_kwargs = {
                "workspace_name": ws.name,
                "client_name": ws.client_name,
            }
            if hasattr(ws, 'client_context') and ws.client_context:
                agent_kwargs["client_context"] = ws.client_context
            
            # For Content Agent, inject cross-project knowledge + workspace memory
            if agent_type == "content":
                try:
                    from admin.agency.content_agent import get_agency_content_agent
                    from admin.workspace.content_store import get_content_store
                    
                    agency_agent = get_agency_content_agent()
                    store = get_content_store()
                    client_ctx = ws.client_context or {}
                    
                    # Get agency knowledge (from ALL workspaces)
                    knowledge = agency_agent.get_knowledge_for_workspace(
                        industry=client_ctx.get("industry", ""),
                    )
                    
                    # Get workspace-specific memory
                    ws_memory = store.get_memory_summary(wid)
                    
                    # Build combined context
                    knowledge_parts = []
                    
                    if knowledge.get("prompt_patterns") or knowledge.get("brand_insights"):
                        knowledge_parts.append(_build_knowledge_context(knowledge))
                    
                    if ws_memory:
                        knowledge_parts.append(ws_memory)
                    
                    # Also add mistakes to avoid from this workspace
                    mem = store.get_or_create(
                        workspace_id=wid,
                        workspace_name=ws.name,
                        client_name=ws.client_name,
                        industry=client_ctx.get("industry", ""),
                    )
                    if mem.mistakes_to_avoid:
                        knowledge_parts.append(
                            "\n## MISTAKES TO AVOID (from this workspace's history)\n"
                            + "\n".join(f"- {m}" for m in mem.mistakes_to_avoid[:5])
                        )
                    
                    if knowledge_parts:
                        knowledge_text = "\n\n".join(knowledge_parts)
                        agent_kwargs["_agency_knowledge"] = knowledge_text
                        logger.info(
                            "Injecting knowledge into Content Agent for workspace '%s': "
                            "agency + workspace memory + %d mistakes to avoid",
                            ws.name, len(mem.mistakes_to_avoid),
                        )
                except Exception as e:
                    logger.warning("Failed to load agency/workspace knowledge: %s", e)

            agent = agent_class(**agent_kwargs)
            response, _ = await agent.chat(message)
            return response
        except TypeError:
            # Fallback: agents that don't accept client_context yet
            try:
                agent = agent_class(workspace_name=ws.name, client_name=ws.client_name)
                response, _ = await agent.chat(message)
                return response
            except Exception as exc2:
                logger.warning("Domain agent %s failed: %s", agent_type, exc2)
        except Exception as exc:
            logger.warning("Domain agent %s failed, falling back to generic: %s", agent_type, exc)

    # Fallback: generic LLM agent (analytics, memory, unknown types)
    from admin.config import settings
    import openai

    client = openai.AsyncOpenAI(
        api_key=settings.WORKSPACE_API_KEY or None,
        base_url=settings.WORKSPACE_API_BASE or None,
    )

    system_prompt = (
        f"You are the {agent_type.upper()} agent for workspace "
        f"'{ws.name}' (client: {ws.client_name}). "
        f"You are a specialist in your domain. Respond helpfully and concisely."
    )

    try:
        resp = await client.chat.completions.create(
            model=settings.WORKSPACE_AGENT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
        )
        return resp.choices[0].message.content or "No response generated."
    except Exception as exc:
        return f"{agent_type.upper()} agent LLM call failed: {exc}"
