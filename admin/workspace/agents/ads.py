"""Ads Agent — Meta (Facebook + Instagram) + Google Ads specialist.

Domain (from interview Q1-Q5):
- Full ownership: strategy → campaign → optimization → reporting
- Meta (Facebook + Instagram) primary, Google Ads secondary
- Auto-optimization loop (budget shift, creative rotation, bid adjustment)
- Multi-layer error recovery
- Prospecting + retargeting hybrid
"""

from __future__ import annotations

import json
import logging
from typing import Annotated, Any, TypedDict

import openai
from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from admin.config import settings

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 5

ADS_SYSTEM_PROMPT = """You are the Ads Agent for workspace '{workspace_name}' (client: {client_name}).

You are a performance marketing specialist focused on paid advertising.

## Your Expertise
- Meta Ads (Facebook + Instagram): campaign strategy, audience targeting, creative direction, budget optimization
- Google Ads: search, display, shopping, performance max campaigns
- ROAS/ROI driven optimization
- Prospecting + retargeting hybrid strategies
- Multi-platform budget allocation

## Your Rules (from interview)
1. You own EVERYTHING — ad copy, creative briefs, budget allocation, optimization
2. For visual creatives, brief Content Agent. You write the copy and strategy.
3. You auto-optimize based on metrics — don't wait for anyone
4. Error recovery: minor fixes first → aggressive optimization → pause → report CEO
5. You think about both prospecting AND retargeting simultaneously
6. You measure success by ROAS/ROI targets per client
7. CEO can override your strategy anytime

## Metrics You Track
- ROAS, ROI, CTR, CPC, CPA, CPM
- Impression Share, Frequency, Reach
- Conversion Rate, Cost per Conversion
- Campaign-level and ad-set-level performance

## What you know about this workspace

{workspace_context}

## Thinking Process
1. What's the advertising goal?
2. What budget/platforms are available?
3. What's the target audience?
4. What approach maximizes ROAS?
5. What's my specific recommendation?
"""


ADS_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_campaign_strategy",
            "description": "Create a comprehensive ad campaign strategy.",
            "parameters": {
                "type": "object",
                "properties": {
                    "platform": {"type": "string", "enum": ["meta", "google", "both"], "description": "Ad platform"},
                    "objective": {"type": "string", "description": "Campaign objective"},
                    "budget": {"type": "string", "description": "Budget allocation plan"},
                    "audience": {"type": "string", "description": "Target audience description"},
                },
                "required": ["platform", "objective"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "brief_content_agent",
            "description": "Brief Content Agent for ad creative visuals.",
            "parameters": {
                "type": "object",
                "properties": {
                    "creative_type": {"type": "string", "description": "Type of creative (image, video, carousel)"},
                    "brief": {"type": "string", "description": "Creative brief"},
                    "platform": {"type": "string", "description": "Target platform"},
                },
                "required": ["creative_type", "brief"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_performance",
            "description": "Analyze campaign performance and suggest optimizations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "metrics": {"type": "string", "description": "Current metrics data"},
                    "period": {"type": "string", "description": "Analysis period"},
                },
                "required": ["metrics"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "report_to_ceo",
            "description": "Report campaign status or strategy to CEO.",
            "parameters": {
                "type": "object",
                "properties": {
                    "report_type": {"type": "string", "enum": ["strategy_proposal", "performance_update", "issue_alert"]},
                    "content": {"type": "string", "description": "Report content"},
                },
                "required": ["report_type", "content"],
            },
        },
    },
]


class AdsAgentState(TypedDict):
    messages: Annotated[list[dict[str, Any]], lambda e, n: e + n]
    workspace_name: str
    client_name: str
    workspace_context: str
    tool_round: int
    final_output: str
    error: str | None


async def ads_call_llm(state: AdsAgentState) -> dict:
    system_prompt = ADS_SYSTEM_PROMPT.format(
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
            tools=ADS_TOOLS,
            tool_choice="auto",
        )
    except Exception as exc:
        logger.exception("Ads Agent LLM call failed")
        return {"error": str(exc), "messages": [], "tool_round": state.get("tool_round", 0)}

    msg = response.choices[0].message
    assistant_msg: dict[str, Any] = {"role": "assistant", "content": msg.content or ""}
    if msg.tool_calls:
        assistant_msg["tool_calls"] = [
            {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
            for tc in msg.tool_calls
        ]
    return {"messages": [assistant_msg], "error": None}


def ads_route(state: AdsAgentState) -> str:
    if state.get("error"):
        return "finalize"
    last = state.get("messages", [{}])[-1]
    if isinstance(last, dict) and last.get("tool_calls"):
        return "run_tools" if state.get("tool_round", 0) < MAX_TOOL_ROUNDS else "finalize"
    return "finalize"


async def ads_run_tools(state: AdsAgentState) -> dict:
    messages = state.get("messages", [])
    last = messages[-1] if messages else {}
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

        if name == "create_campaign_strategy":
            result_text = f"Campaign strategy created for {args.get('platform', 'N/A')}:\nObjective: {args.get('objective', 'N/A')}\nBudget: {args.get('budget', 'TBD')}\nAudience: {args.get('audience', 'TBD')}"
        elif name == "brief_content_agent":
            result_text = f"Creative brief sent to Content Agent:\nType: {args.get('creative_type', 'N/A')}\nBrief: {args.get('brief', 'N/A')[:200]}"
        elif name == "analyze_performance":
            result_text = f"Performance analysis:\nMetrics: {args.get('metrics', 'N/A')[:300]}\n[Detailed analysis would appear here]"
        elif name == "report_to_ceo":
            result_text = f"Report sent to CEO ({args.get('report_type', 'N/A')}):\n{args.get('content', 'N/A')[:200]}"
        else:
            result_text = f"Unknown tool: {name}"

        results.append({"role": "tool", "tool_call_id": tc.get("id", ""), "content": result_text})
    return {"messages": results, "tool_round": state.get("tool_round", 0) + 1}


async def ads_finalize(state: AdsAgentState) -> dict:
    for msg in reversed(state.get("messages", [])):
        if isinstance(msg, dict) and msg.get("role") == "assistant" and msg.get("content"):
            return {"final_output": msg["content"]}
    if state.get("error"):
        return {"final_output": f"Ads Agent error: {state['error'][:200]}"}
    return {"final_output": "Ads Agent analysis complete."}


def build_ads_graph() -> StateGraph:
    workflow = StateGraph(AdsAgentState)
    workflow.add_node("call_llm", ads_call_llm)
    workflow.add_node("run_tools", ads_run_tools)
    workflow.add_node("finalize", ads_finalize)
    workflow.set_entry_point("call_llm")
    workflow.add_conditional_edges("call_llm", ads_route, {"run_tools": "run_tools", "finalize": "finalize"})
    workflow.add_edge("run_tools", "call_llm")
    workflow.add_edge("finalize", END)
    return workflow.compile(checkpointer=MemorySaver())


class AdsAgent:
    """Ads Agent for a specific workspace."""

    def __init__(self, workspace_name: str = "Default", client_name: str = "Client"):
        self.graph = build_ads_graph()
        self.workspace_name = workspace_name
        self.client_name = client_name
        self._thread_id = f"ads_{workspace_name}"

    async def chat(self, message: str) -> tuple[str, str]:
        workspace_context = f"Workspace: {self.workspace_name}, Client: {self.client_name}"
        initial_state = {
            "messages": [{"role": "user", "content": message}],
            "workspace_name": self.workspace_name,
            "client_name": self.client_name,
            "workspace_context": workspace_context,
            "tool_round": 0, "final_output": "", "error": None,
        }
        try:
            result = await self.graph.ainvoke(initial_state, config={"configurable": {"thread_id": self._thread_id}})
        except Exception:
            logger.exception("Ads Agent execution failed")
            return "Ads Agent temporarily unavailable.", self._thread_id
        return result.get("final_output", "Ads Agent analysis complete."), self._thread_id
