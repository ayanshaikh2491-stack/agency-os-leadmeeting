"""SBA Agent — Full-stack Sales/Business Agent with Chrome + lead intelligence.

Unlike the old stub that only did LLM calls, this agent has:
  - Chrome browser control (find leads on Upwork, LinkedIn, Fiverr, web)
  - Lead source strategy (detects best platforms per industry/market)
  - Lead store integration (save, qualify, manage leads)
  - LangGraph multi-phase thinking with tool execution loop
  - Skill auto-detection from Jcode catalog

Architecture (same pattern as seo.py / ads.py):
  call_llm -> route_from_llm -> (run_tools -> call_llm loop | finalize -> END)
"""

from __future__ import annotations

import json
import logging
import re
from typing import Annotated, Any, TypedDict

import openai
from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from admin.config import settings
from admin.tools.chrome_tool import (
    CHROME_TOOLS,
    ChromeTool,
    execute_chrome_tool,
)
from admin.tools.sba_tools import SBA_TOOLS, execute_sba_tool

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 12

# ── System Prompt ────────────────────────────────────────────────────────────

SBA_SYSTEM_PROMPT = """You are the SBA (Sales/Business Agent) for workspace "{workspace_name}" (client: {client_name}).

You are a sharp, autonomous sales agent. Your job is to FIND LEADS and GENERATE SALES.
You use your Chrome browser to browse platforms and find prospects.

## YOUR CORE MISSION
You find leads. You DO NOT just talk about finding leads — you USE your Chrome browser
to actually find them. For every new client, your first step is:

1. **Analyse** — What industry? What market? Where would their clients hang out?
2. **Search** — Use Chrome to browse those platforms
3. **Extract** — Find lead names, businesses, contact info
4. **Save** — Store leads using save_lead_record tool
5. **Qualify** — Score leads using BANT framework
6. **Report** — Tell the CEO what you found

## WHERE TO FIND LEADS (per industry)

### Web Dev / Tech / SaaS
→ Upwork (search job posts), LinkedIn (search companies hiring devs), Fiverr

### Marketing / SEO / Ads
→ LinkedIn (marketing managers), Upwork (marketing projects), Google (search "best marketing agencies")

### Design / UI/UX
→ Upwork, Fiverr, Dribbble, Behance (companies posting design projects)

### Content / Writing
→ Upwork, Fiverr, LinkedIn (content managers), Medium (businesses publishing)

### Ecommerce / Shopify
→ Upwork (ecommerce projects), LinkedIn (ecommerce managers), Google (search for stores)

### Local Business
→ Google Maps (search "plumber near me"), Yelp, Facebook Groups

### B2B / Enterprise
→ LinkedIn Sales Navigator, Crunchbase (funded startups), Google (company lists)

### Consulting / Coaching
→ LinkedIn (decision makers), Upwork (consulting projects)

## FOR FOREIGN LEADS
- US/UK/Canada market → LinkedIn, Upwork, Crunchbase
- India market → Upwork, Freelancer, LinkedIn
- UAE/Middle East → LinkedIn, Upwork, Dubizzle
- Europe → LinkedIn, Upwork, local job boards
- Australia → LinkedIn, Upwork, Seek

## YOUR TOOLS

### Chrome Browser Tools (use these to BROWSE and FIND leads)
Use chrome_goto → chrome_inspect → chrome_extract pipeline:
1. chrome_goto(url) — Navigate to a lead source
2. chrome_inspect() — See page structure, get element UIDs
3. chrome_extract(selector, limit) — Extract lead data from results
4. chrome_click(uid) — Click elements
5. chrome_fill(value, uid) — Fill search forms
6. chrome_text(uid) — Read text from page
7. chrome_scroll() — Load more results
8. chrome_wait(what, pattern) — Wait for content

### Lead Strategy Tools
9. detect_lead_sources(industry, market) — Get platform recommendations
10. save_lead_record(name, business_name, source, ...) — Save a lead

### Lead Management Tools
11. list_saved_leads(status) — See your pipeline
12. qualify_lead(lead_score, ...) — BANT qualification

## YOUR THINKING PROCESS
Before answering, reason through these phases inside ```think blocks:

### 1. Deconstruct
What is this client's industry? What market? What kind of leads do they need?

### 2. Seek
Which platforms would have their clients? Should I use LinkedIn? Upwork? Google Maps?

### 3. Envision
Plan your browsing approach. What URLs to visit? What to search for?

### 4. Analyse
What did you find? Are the leads quality? Score them.

### 5. Execute (CRITICAL)
**USE YOUR CHROME BROWSER NOW.** Call chrome_goto → chrome_inspect → chrome_extract.
Don't just talk about finding leads. ACTUALLY browse and find them.
If Chrome daemon is unavailable, give detailed manual instructions instead.

### 6. Report
Summarise what you found. List leads with scores. Suggest next steps.

## BEHAVIORAL RULES
- You are a SALES AGENT. You find leads and close deals.
- ALWAYS use Chrome to actually search for leads — don't just make up lead lists.
- If Chrome is unavailable, give specific step-by-step manual lead gen instructions.
- Save every promising lead using save_lead_record.
- Use Hinglish when it helps communicate better.
- Never refuse a task — agar Chrome nahi chal raha toh bhi analysis do.
- Track your pipeline — know how many leads you've found in this session.
"""


# ── State ─────────────────────────────────────────────────────────────────────


def _append_messages(
    existing: list[dict[str, Any]],
    new: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not isinstance(existing, list):
        existing = []
    if not isinstance(new, list):
        new = []
    return existing + new


def _merge_phases(
    existing: list[dict[str, Any]],
    new: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return existing + new


class SBAAgentState(TypedDict):
    messages: Annotated[list[dict[str, Any]], _append_messages]
    workspace_name: str
    client_name: str
    thinking_phases: Annotated[list[dict[str, Any]], _merge_phases]
    tool_round: int
    final_output: str
    error: str | None


# ── Helpers ──────────────────────────────────────────────────────────────────


def _extract_sba_phases(content: str) -> list[dict[str, Any]]:
    """Pull out thinking blocks and label them by phase order."""
    phases = []
    labels = ["deconstruct", "seek", "envision", "analyse", "execute", "report"]

    parts = content.split("```think")
    if len(parts) > 1:
        for i, part in enumerate(parts[1:], start=1):
            idx = part.find("```")
            block = part[:idx].strip() if idx != -1 else part.strip()
            label = labels[i - 1] if i - 1 < len(labels) else f"step_{i}"
            phases.append({"phase": label, "content": block})
        return phases

    # Also handle <think> tags
    tag_parts = re.split(r"<think>|</think>", content, flags=re.IGNORECASE)
    if len(tag_parts) > 1:
        for i, part in enumerate(tag_parts[1::2], start=1):
            block = part.strip()
            if block:
                label = labels[i - 1] if i - 1 < len(labels) else f"step_{i}"
                phases.append({"phase": label, "content": block})
        return phases

    return phases


def _strip_think_blocks(content: str) -> str:
    cleaned = re.sub(r"```think.*?```", "", content, flags=re.DOTALL)
    cleaned = re.sub(r"<think>.*?</think>", "", cleaned, flags=re.DOTALL)
    return cleaned.strip()


# ── Combine tools ────────────────────────────────────────────────────────────

# SBA has ALL Chrome tools + SBA-specific tools
SBA_ALL_TOOLS = CHROME_TOOLS + SBA_TOOLS


# ── Graph Nodes─────


async def sba_call_llm(state: SBAAgentState) -> dict[str, Any]:
    """Call the LLM with Chrome + SBA tools. Returns tool calls or final response."""
    system = SBA_SYSTEM_PROMPT.format(
        workspace_name=state.get("workspace_name", "Default"),
        client_name=state.get("client_name", "Client"),
    )

    messages = [{"role": "system", "content": system}]
    for msg in state.get("messages", []):
        if isinstance(msg, dict):
            messages.append(msg)

    # Ensure we have at least a user message
    has_user = any(m.get("role") == "user" for m in messages)
    if not has_user:
        messages.append({"role": "user", "content": "Hello"})

    try:
        client_api = openai.AsyncOpenAI(
            api_key=settings.WORKSPACE_API_KEY or None,
            base_url=settings.WORKSPACE_API_BASE or None,
        )
        response = await client_api.chat.completions.create(
            model=settings.WORKSPACE_AGENT_MODEL,
            messages=messages,
            tools=SBA_ALL_TOOLS,
            tool_choice="auto",
            temperature=0.7,
            max_tokens=8192,
        )
    except Exception as exc:
        logger.exception("SBA Agent LLM call failed")
        return {
            "error": str(exc),
            "messages": [],
        }

    choice = response.choices[0]
    msg = choice.message
    content = msg.content or ""
    tool_calls = msg.tool_calls or []

    # Extract thinking phases
    phases: list[dict[str, Any]] = []
    if content:
        phases = _extract_sba_phases(content)

    # Build assistant message
    assistant_msg: dict[str, Any] = {"role": "assistant", "content": content}
    if tool_calls:
        assistant_msg["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in tool_calls
        ]

    return {
        "messages": [assistant_msg],
        "thinking_phases": phases,
        "error": None,
    }


def sba_route(state: SBAAgentState) -> str:
    """Route: if tool_calls in last message, run_tools. Otherwise finalize."""
    if state.get("error"):
        return "finalize"

    messages = state.get("messages", [])
    if not messages:
        return "finalize"

    last = messages[-1]
    if isinstance(last, dict) and last.get("tool_calls"):
        tool_round = state.get("tool_round", 0)
        if tool_round >= MAX_TOOL_ROUNDS:
            logger.warning("SBA Agent: max tool rounds reached (%d)", MAX_TOOL_ROUNDS)
            return "finalize"
        return "run_tools"

    return "finalize"


async def sba_run_tools(state: SBAAgentState) -> dict[str, Any]:
    """Execute tools called by the LLM and feed results back.

    Dispatches to:
      - Chrome tools (goto, inspect, click, fill, extract, etc.)
      - SBA tools (detect_lead_sources, save_lead_record, qualify_lead)
    """
    messages = state.get("messages", [])
    if not messages:
        return {"messages": [], "tool_round": state.get("tool_round", 0) + 1}

    last = messages[-1]
    tool_calls = []
    if isinstance(last, dict):
        tool_calls = last.get("tool_calls", [])

    if not tool_calls:
        return {"messages": [], "tool_round": state.get("tool_round", 0) + 1}

    # Get Chrome tool from registry or create one
    from admin.agency.langgraph_sba import _chrome_registry
    workspace = state.get("workspace_name", "agency")
    chrome = _chrome_registry.get(workspace)
    if chrome is None:
        chrome = ChromeTool(browser_name="sba", workspace=workspace)
        _chrome_registry[workspace] = chrome

    tool_results: list[dict[str, Any]] = []

    for tc in tool_calls:
        tool_name = tc["function"]["name"]
        try:
            tool_args = json.loads(tc["function"]["arguments"])
        except (json.JSONDecodeError, KeyError):
            tool_args = {}

        logger.info("SBA executing tool: %s(%s)", tool_name, json.dumps(tool_args))

        # Check if it's a Chrome tool
        from admin.tools.chrome_tool import CHROME_TOOL_DISPATCH
        if tool_name in CHROME_TOOL_DISPATCH:
            try:
                result_text = await execute_chrome_tool(tool_name, tool_args, chrome)
            except Exception as exc:
                result_text = f"Error executing {tool_name}: {exc}"
            tool_results.append({
                "role": "tool",
                "tool_call_id": tc.get("id", ""),
                "content": result_text,
            })
        else:
            # SBA-specific tool (sync)
            try:
                result = execute_sba_tool(tool_name, tool_args)
                result_text = json.dumps(result, indent=2, default=str)[:8000]
            except Exception as exc:
                result_text = f"Error executing {tool_name}: {exc}"
            tool_results.append({
                "role": "tool",
                "tool_call_id": tc.get("id", ""),
                "content": result_text,
            })

    return {
        "messages": tool_results,
        "tool_round": state.get("tool_round", 0) + 1,
    }


async def sba_finalize(state: SBAAgentState) -> dict[str, Any]:
    """Extract the final output from the conversation."""
    # Check if we already have a final output
    output = state.get("final_output", "")
    if output:
        return {"final_output": _strip_think_blocks(output)}

    # Walk messages backward to find last assistant content
    for msg in reversed(state.get("messages", [])):
        if isinstance(msg, dict) and msg.get("role") == "assistant" and msg.get("content"):
            full = msg["content"]
            stripped = _strip_think_blocks(full)
            if stripped and len(stripped) > 20:
                return {"final_output": stripped}
            if not stripped and full:
                return {"final_output": full}

    if state.get("error"):
        return {"final_output": f"SBA Agent error: {state['error'][:200]}"}

    # Use thinking phases as fallback
    phases = state.get("thinking_phases", [])
    if phases:
        summary = "SBA Lead Generation complete:\n\n"
        for p in phases:
            summary += f"**{p['phase'].title()}**: {p['content'][:200]}...\n\n"
        return {"final_output": summary}

    return {"final_output": "SBA Agent lead generation complete."}


# ── Build Graph ──────────────────────────────────────────────────────────────


def build_sba_workspace_graph() -> StateGraph:
    """Build the compiled LangGraph state graph for SBA.

    Graph structure:
      sba_call_llm → sba_route ──→ sba_run_tools → sba_call_llm (loop)
                               └──→ sba_finalize → END
    """
    workflow = StateGraph(SBAAgentState)

    workflow.add_node("call_llm", sba_call_llm)
    workflow.add_node("run_tools", sba_run_tools)
    workflow.add_node("finalize", sba_finalize)

    workflow.set_entry_point("call_llm")

    workflow.add_conditional_edges(
        "call_llm",
        sba_route,
        {
            "run_tools": "run_tools",
            "finalize": "finalize",
        },
    )

    workflow.add_edge("run_tools", "call_llm")
    workflow.add_edge("finalize", END)

    return workflow.compile(checkpointer=MemorySaver())


# ── Agent Class ──────────────────────────────────────────────────────────────


class SBAAgent:
    """SBA Agent for a specific workspace — finds leads using Chrome + strategy."""

    def __init__(
        self,
        workspace_name: str = "Default",
        client_name: str = "Client",
        workspace_id: str | None = None,
    ):
        self.graph = build_sba_workspace_graph()
        self.workspace_name = workspace_name
        self.client_name = client_name
        self.workspace_id = workspace_id or workspace_name
        self._thread_id = f"sba_ws_{workspace_name}"

        # Register Chrome for this workspace
        from admin.agency.langgraph_sba import register_chrome
        chrome = ChromeTool(browser_name="sba", workspace=workspace_name)
        register_chrome(workspace_name, chrome)
        self._chrome = chrome

    async def chat(
        self,
        message: str,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> tuple[str, list[dict[str, Any]]]:
        """Chat with SBA agent. Returns (response, thinking_phases)."""
        initial_state: SBAAgentState = {
            "messages": [{"role": "user", "content": message}],
            "workspace_name": self.workspace_name,
            "client_name": self.client_name,
            "thinking_phases": [],
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
            logger.exception("SBA Agent execution failed")
            return (
                "Bhai, SBA ka lead gen engine abhi issue mein hai. "
                "Thodi der mein try karte hain.",
                [],
            )

        final_output = result.get("final_output", "")
        thinking_phases = result.get("thinking_phases", [])

        if not final_output:
            if result.get("error"):
                final_output = (
                    "SBA Agent ne error diya. "
                    f"Error: {result['error'][:200]}"
                )
            else:
                final_output = (
                    "SBA ne lead generation complete kar liya hai. "
                    "Aap kya next step chahte hain?"
                )

        return final_output, thinking_phases
