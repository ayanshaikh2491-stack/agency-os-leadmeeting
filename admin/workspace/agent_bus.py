"""Inter-agent communication bus.

Enables:
  - Agent-to-agent briefs (SEO -> Content, Ads -> Content, etc.)
  - CEO parallel blast (brief all agents simultaneously)
  - Cross-workspace knowledge sharing
  - Message history and audit trail

Architecture:
  Each agent can SEND briefs to other agents within the same workspace.
  The CEO can BROADCAST to all agents in a workspace.
  Knowledge learned in one workspace can be SHARED across workspaces.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


# ── Message Types ─────────────────────────────────────────────────────────────


@dataclass
class AgentMessage:
    """A message sent between agents."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    from_agent: str = ""
    to_agent: str = ""
    workspace_id: str = ""
    message_type: str = "brief"  # brief, request, response, alert, knowledge
    subject: str = ""
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    read: bool = False
    responded: bool = False


# ── In-Memory Message Store ───────────────────────────────────────────────────

# workspace_id -> list of messages
_messages: dict[str, list[AgentMessage]] = {}

# workspace_id -> knowledge base (cross-workspace sharing)
_knowledge: dict[str, dict[str, Any]] = {}


# ── Send Messages ─────────────────────────────────────────────────────────────


def send_message(
    from_agent: str,
    to_agent: str,
    workspace_id: str,
    subject: str,
    content: str,
    message_type: str = "brief",
    metadata: dict[str, Any] | None = None,
) -> AgentMessage:
    """Send a message from one agent to another within a workspace."""
    msg = AgentMessage(
        from_agent=from_agent,
        to_agent=to_agent,
        workspace_id=workspace_id,
        message_type=message_type,
        subject=subject,
        content=content,
        metadata=metadata or {},
    )

    if workspace_id not in _messages:
        _messages[workspace_id] = []
    _messages[workspace_id].append(msg)

    logger.info(
        "Agent message: %s -> %s [%s] %s",
        from_agent, to_agent, message_type, subject,
    )
    return msg


def get_messages(
    workspace_id: str,
    to_agent: str | None = None,
    from_agent: str | None = None,
    unread_only: bool = False,
    message_type: str | None = None,
) -> list[AgentMessage]:
    """Retrieve messages for a workspace with optional filters."""
    msgs = _messages.get(workspace_id, [])

    if to_agent:
        msgs = [m for m in msgs if m.to_agent == to_agent]
    if from_agent:
        msgs = [m for m in msgs if m.from_agent == from_agent]
    if unread_only:
        msgs = [m for m in msgs if not m.read]
    if message_type:
        msgs = [m for m in msgs if m.message_type == message_type]

    return msgs


def mark_read(message_id: str, workspace_id: str) -> bool:
    """Mark a message as read."""
    for msg in _messages.get(workspace_id, []):
        if msg.id == message_id:
            msg.read = True
            return True
    return False


def mark_responded(message_id: str, workspace_id: str) -> bool:
    """Mark a message as responded to."""
    for msg in _messages.get(workspace_id, []):
        if msg.id == message_id:
            msg.responded = True
            return True
    return False


# ── Agent Briefing (used by CEO and agents) ───────────────────────────────────


def brief_agent(
    from_agent: str,
    to_agent: str,
    workspace_id: str,
    task: str,
    context: str = "",
    priority: str = "normal",
) -> AgentMessage:
    """Send a task brief from one agent to another.

    This is the primary communication method:
    - CEO briefs sub-agents (delegation)
    - SEO briefs Content (content requests)
    - Ads briefs Content (creative requests)
    - Social briefs Content (visual requests)
    """
    content = f"**Task:** {task}"
    if context:
        content += f"\n\n**Context:** {context}"
    content += f"\n\n**Priority:** {priority}"

    return send_message(
        from_agent=from_agent,
        to_agent=to_agent,
        workspace_id=workspace_id,
        subject=f"Brief from {from_agent}: {task[:80]}",
        content=content,
        message_type="brief",
        metadata={"priority": priority, "context": context},
    )


def respond_to_brief(
    from_agent: str,
    to_agent: str,
    workspace_id: str,
    original_message_id: str,
    response: str,
) -> AgentMessage:
    """Respond to a brief received from another agent."""
    # Mark original as responded
    mark_responded(original_message_id, workspace_id)

    return send_message(
        from_agent=from_agent,
        to_agent=to_agent,
        workspace_id=workspace_id,
        subject=f"Response from {from_agent}",
        content=response,
        message_type="response",
        metadata={"in_reply_to": original_message_id},
    )


# ── CEO Parallel Blast ────────────────────────────────────────────────────────


def parallel_blast(
    workspace_id: str,
    task: str,
    context: str = "",
    agents: list[str] | None = None,
    from_agent: str = "ceo",
) -> list[AgentMessage]:
    """Brief ALL agents in a workspace simultaneously (Q4).

    CEO uses this to delegate a task to all sub-agents at once.
    Each agent receives the same brief and works independently.
    """
    if agents is None:
        agents = ["sba", "seo", "content", "website", "ads", "social", "analytics"]

    messages = []
    for agent in agents:
        msg = brief_agent(
            from_agent=from_agent,
            to_agent=agent,
            workspace_id=workspace_id,
            task=task,
            context=context,
            priority="high",
        )
        messages.append(msg)

    logger.info(
        "Parallel blast to %d agents in workspace %s",
        len(messages), workspace_id,
    )
    return messages


# ── Cross-Workspace Knowledge Sharing ─────────────────────────────────────────


def share_knowledge(
    workspace_id: str,
    key: str,
    value: Any,
    source_agent: str = "",
    category: str = "general",
) -> None:
    """Share a learning/insight from one workspace.

    This knowledge can be retrieved by other workspaces
    to avoid repeating mistakes and share best practices.
    """
    if workspace_id not in _knowledge:
        _knowledge[workspace_id] = {}

    _knowledge[workspace_id][key] = {
        "value": value,
        "source_agent": source_agent,
        "category": category,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    logger.info(
        "Knowledge shared from workspace %s: %s = %s",
        workspace_id, key, str(value)[:100],
    )


def get_knowledge(
    workspace_id: str,
    key: str | None = None,
    category: str | None = None,
) -> dict[str, Any]:
    """Retrieve shared knowledge for a workspace."""
    ws_knowledge = _knowledge.get(workspace_id, {})

    if key:
        return {key: ws_knowledge[key]} if key in ws_knowledge else {}

    if category:
        return {
            k: v for k, v in ws_knowledge.items()
            if v.get("category") == category
        }

    return ws_knowledge


def get_all_knowledge() -> dict[str, dict[str, Any]]:
    """Get all shared knowledge across all workspaces."""
    return dict(_knowledge)


# ── Communication Summary (for CEO dashboard) ─────────────────────────────────


def get_communication_summary(workspace_id: str) -> dict[str, Any]:
    """Get a summary of all agent communications in a workspace."""
    msgs = _messages.get(workspace_id, [])

    # Count by agent
    sent_by: dict[str, int] = {}
    received_by: dict[str, int] = {}
    for msg in msgs:
        sent_by[msg.from_agent] = sent_by.get(msg.from_agent, 0) + 1
        received_by[msg.to_agent] = received_by.get(msg.to_agent, 0) + 1

    # Count by type
    by_type: dict[str, int] = {}
    for msg in msgs:
        by_type[msg.message_type] = by_type.get(msg.message_type, 0) + 1

    # Unread count
    unread = sum(1 for m in msgs if not m.read)

    return {
        "total_messages": len(msgs),
        "sent_by": sent_by,
        "received_by": received_by,
        "by_type": by_type,
        "unread": unread,
        "recent_messages": [
            {
                "from": m.from_agent,
                "to": m.to_agent,
                "subject": m.subject,
                "type": m.message_type,
                "timestamp": m.timestamp,
            }
            for m in msgs[-10:]  # Last 10 messages
        ],
    }
