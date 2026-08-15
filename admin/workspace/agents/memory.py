"""Memory Agent — Workspace-wide key/value memory keeper.

Domain (from interview):
- Remember client preferences, learned facts, and per-agent state across runs
- Recall anything the workspace has previously stored
- Surface memory held by other agents (sba, seo, content, ...) in the workspace

This agent is the conversational wrapper around the existing durable memory
infra in admin.agency.agent_persistence. It does NOT introduce a new storage
layer — it reuses the per-workspace, per-agent key/value store that the other
agents already write to.
"""

from __future__ import annotations

import json
import logging
from typing import Annotated, Any, TypedDict

import openai
from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from admin.agency.agent_persistence import get_checkpointer
from admin.config import settings
from admin.tools.memory_tools import MEMORY_TOOLS, execute_memory_tool
from admin.workspace.agent_bus import send_message

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 5


MEMORY_SYSTEM_PROMPT = """You are the Memory Agent for workspace '{workspace_name}' (client: {client_name}).

You are the workspace's long-term memory keeper. Other agents store their
learnings, state, and client preferences in per-agent memory; you help the
CEO and the team read, write, and forget that memory.

## Your Expertise
- Remembering explicit instructions ("remember that this client hates em-dashes")
- Recalling stored facts, preferences, and prior decisions
- Surfacing what other agents (sba, seo, content, website, ads, social, analytics)
  have learned in this workspace
- Keeping the workspace's institutional knowledge tidy and queryable

## Your Rules (from interview)
1. When the user asks you to "remember" something, SAVE it under a clear key.
2. When the user asks "what do we know about X", LIST or GET the relevant memory.
3. Prefer recall_others to pull context from sibling agents before answering
   knowledge questions about the client or past work.
4. Never invent memories — only report what is actually stored. If nothing is
   stored, say so plainly.
5. You are the source of truth for durable workspace facts — be concise and exact.

## Your 5 Tools
- save_memory: store a key/value memory for this workspace
- get_memory: retrieve one memory value by key
- list_memory: list all keys you hold for this workspace
- delete_memory: forget one memory (or all, if key omitted)
- recall_others: read memory held by another agent in this workspace

## What you know about this workspace

{workspace_context}

## Thinking Process
1. Does the user want to store, retrieve, or forget?
2. Which key/target agent is involved?
3. Call the matching tool and report the real result (no fabrication).
"""


class MemoryAgentState(TypedDict):
    messages: Annotated[list[dict[str, Any]], lambda e, n: e + n]
    workspace_name: str
    client_name: str
    workspace_context: str
    tool_round: int
    final_output: str
    error: str | None


async def memory_call_llm(state: MemoryAgentState) -> dict:
    """Call LLM with Memory agent system prompt."""
    system_prompt = MEMORY_SYSTEM_PROMPT.format(
        workspace_name=state.get("workspace_name", "Unknown"),
        client_name=state.get("client_name", "Unknown"),
        workspace_context=state.get("workspace_context", "No data yet."),
    )

    messages = [{"role": "system", "content": system_prompt}]
    for msg in state.get("messages", []):
        if isinstance(msg, dict):
            messages.append(msg)

    if not any(m.get("role") == "user" for m in messages):
        messages.append({"role": "user", "content": "Hello"})

    try:
        client_api = openai.AsyncOpenAI(
            api_key=settings.WORKSPACE_API_KEY or None,
            base_url=settings.WORKSPACE_API_BASE or None,
        )
        response = await client_api.chat.completions.create(
            model=settings.WORKSPACE_AGENT_MODEL,
            messages=messages,
            tools=MEMORY_TOOLS,
            tool_choice="auto",
        )
    except Exception as exc:
        logger.exception("Memory Agent LLM call failed")
        return {"error": str(exc), "messages": [], "tool_round": state.get("tool_round", 0)}

    msg = response.choices[0].message

    assistant_msg: dict[str, Any] = {"role": "assistant", "content": msg.content or ""}
    if msg.tool_calls:
        assistant_msg["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {"name": tc.function.name, "arguments": tc.function.arguments},
            }
            for tc in msg.tool_calls
        ]

    return {"messages": [assistant_msg], "error": None}


def memory_route(state: MemoryAgentState) -> str:
    if state.get("error"):
        return "finalize"
    messages = state.get("messages", [])
    if not messages:
        return "finalize"
    last = messages[-1]
    if isinstance(last, dict) and last.get("tool_calls"):
        if state.get("tool_round", 0) >= MAX_TOOL_ROUNDS:
            return "finalize"
        return "run_tools"
    return "finalize"


async def memory_run_tools(state: MemoryAgentState) -> dict:
    """Execute Memory tools using the real tool executor."""
    messages = state.get("messages", [])
    if not messages:
        return {"messages": [], "tool_round": state.get("tool_round", 0) + 1}

    last = messages[-1]
    tool_calls = last.get("tool_calls", []) if isinstance(last, dict) else []
    if not tool_calls:
        return {"messages": [], "tool_round": state.get("tool_round", 0) + 1}

    results = []
    for tc in tool_calls:
        name = tc["function"]["name"]
        try:
            args = json.loads(tc["function"]["arguments"])
        except (json.JSONDecodeError, KeyError):
            args = {}

        # Always bind the workspace so tool handlers know the scope.
        args.setdefault("workspace", state.get("workspace_name", "Default"))

        tool_result = execute_memory_tool(name, args)
        result_text = json.dumps(tool_result, indent=2, default=str)

        results.append({"role": "tool", "tool_call_id": tc.get("id", ""), "content": result_text})

    return {"messages": results, "tool_round": state.get("tool_round", 0) + 1}


async def memory_finalize(state: MemoryAgentState) -> dict:
    messages = state.get("messages", [])
    for msg in reversed(messages):
        if isinstance(msg, dict) and msg.get("role") == "assistant" and msg.get("content"):
            return {"final_output": msg["content"]}

    if state.get("error"):
        return {"final_output": f"Memory Agent error: {state['error'][:200]}"}
    return {"final_output": "Memory Agent done."}


def build_memory_graph(checkpointer=None) -> StateGraph:
    workflow = StateGraph(MemoryAgentState)
    workflow.add_node("call_llm", memory_call_llm)
    workflow.add_node("run_tools", memory_run_tools)
    workflow.add_node("finalize", memory_finalize)
    workflow.set_entry_point("call_llm")
    workflow.add_conditional_edges("call_llm", memory_route, {
        "run_tools": "run_tools", "finalize": "finalize",
    })
    workflow.add_edge("run_tools", "call_llm")
    workflow.add_edge("finalize", END)
    return workflow.compile(checkpointer=checkpointer or MemorySaver())


class MemoryAgent:
    """Memory Agent for a specific workspace."""

    def __init__(self, workspace_name: str = "Default", client_name: str = "Client"):
        self.workspace_name = workspace_name
        self.client_name = client_name
        self.graph = build_memory_graph(get_checkpointer(self.workspace_name, "memory"))
        self._thread_id = f"memory_{workspace_name}"

    async def chat(self, message: str) -> tuple[str, str]:
        """Chat with Memory agent. Returns (response, thread_id)."""
        workspace_context = f"Workspace: {self.workspace_name}, Client: {self.client_name}"

        initial_state = {
            "messages": [{"role": "user", "content": message}],
            "workspace_name": self.workspace_name,
            "client_name": self.client_name,
            "workspace_context": workspace_context,
            "tool_round": 0,
            "final_output": "",
            "error": None,
        }

        try:
            result = await self.graph.ainvoke(
                initial_state,
                config={"configurable": {"thread_id": self._thread_id}},
            )
        except Exception:
            logger.exception("Memory Agent execution failed")
            return "Memory Agent temporarily unavailable.", self._thread_id

        return result.get("final_output", "Memory Agent done."), self._thread_id

    def report_to_ceo(self, content: str = "") -> dict[str, Any]:
        """Send a memory summary/alert to CEO via agent_bus."""
        try:
            send_message(
                from_agent="memory",
                to_agent="ceo",
                workspace_id=self.workspace_name,
                subject=f"Memory update: {self.client_name}",
                content=content,
                message_type="report",
            )
            return {"status": "sent", "to": "ceo"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
