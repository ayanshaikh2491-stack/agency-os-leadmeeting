"""Analytics Agent — Performance tracking, reporting, data visualization.

Domain (from interview):
- Track client performance metrics (SEO rankings, ad ROAS, social engagement, website traffic)
- Generate weekly/monthly reports
- Data-driven insights and recommendations
- Cross-channel analytics (combine SEO + Ads + Social data)
- Automated monitoring with alerts
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


# ── Analytics Agent System Prompt ─────────────────────────────────────────────

ANALYTICS_SYSTEM_PROMPT = """You are the Analytics Agent for workspace '{workspace_name}' (client: {client_name}).

You are a data analytics specialist who tracks performance and generates insights.

## Your Expertise
- Performance tracking (SEO rankings, ad ROAS, social engagement, website traffic)
- Data visualization and reporting (weekly, monthly, custom periods)
- Cross-channel analytics (combine data from SEO, Ads, Social, Website)
- Conversion tracking and attribution
- Competitor benchmarking
- ROI analysis and forecasting
- Anomaly detection and alerting

## Your Rules (from interview)
1. You track ALL channels — SEO, Ads, Social, Website — in one dashboard
2. You generate automated weekly/monthly reports
3. You alert CEO/anomalies (traffic drops, ranking losses, ad spend spikes)
4. You provide data-driven recommendations, not just numbers
5. You learn from historical data — identify trends over time
6. You can pull data from any agent's output for cross-channel analysis
7. CEO can request custom reports anytime

## Report Types
- **Weekly Digest**: All channels summary, key metrics, trends
- **Monthly Deep Dive**: Detailed analysis, YoY comparison, recommendations
- **Campaign Report**: Specific campaign/ad performance
- **SEO Report**: Rankings, traffic, backlinks, technical health
- **Social Report**: Engagement, growth, content performance
- **Custom Report**: CEO-requested specific analysis

## What you know about this workspace

{workspace_context}

## Thinking Process
1. What data/metrics are being requested?
2. What channels are involved?
3. What's the time period?
4. What trends or anomalies exist?
5. What actionable insights can I provide?
"""

ANALYTICS_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "generate_report",
            "description": "Generate a performance report for the workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "report_type": {
                        "type": "string",
                        "enum": ["weekly", "monthly", "campaign", "seo", "social", "custom"],
                        "description": "Type of report to generate",
                    },
                    "period": {"type": "string", "description": "Reporting period (e.g., 'last 7 days', 'July 2026')"},
                    "channels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Channels to include (seo, ads, social, website)",
                    },
                },
                "required": ["report_type"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "track_metric",
            "description": "Track a specific metric over time.",
            "parameters": {
                "type": "object",
                "properties": {
                    "metric_name": {"type": "string", "description": "Name of the metric to track"},
                    "current_value": {"type": "string", "description": "Current value"},
                    "previous_value": {"type": "string", "description": "Previous period value for comparison"},
                    "channel": {"type": "string", "description": "Channel this metric belongs to"},
                },
                "required": ["metric_name", "current_value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "detect_anomaly",
            "description": "Report a performance anomaly that needs attention.",
            "parameters": {
                "type": "object",
                "properties": {
                    "metric": {"type": "string", "description": "Metric with anomaly"},
                    "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"], "description": "Anomaly severity"},
                    "description": {"type": "string", "description": "What's abnormal"},
                    "suggested_action": {"type": "string", "description": "Recommended action"},
                },
                "required": ["metric", "severity", "description"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "report_to_ceo",
            "description": "Send analytics insights or alerts to CEO.",
            "parameters": {
                "type": "object",
                "properties": {
                    "report_type": {"type": "string", "enum": ["insight", "alert", "recommendation", "report_ready"]},
                    "content": {"type": "string"},
                },
                "required": ["report_type", "content"],
            },
        },
    },
]


# ── State ─────────────────────────────────────────────────────────────────────


class AnalyticsAgentState(TypedDict):
    messages: Annotated[list[dict[str, Any]], lambda e, n: e + n]
    workspace_name: str
    client_name: str
    workspace_context: str
    tool_round: int
    final_output: str
    error: str | None


# ── Graph Nodes ───────────────────────────────────────────────────────────────


async def analytics_call_llm(state: AnalyticsAgentState) -> dict:
    """Call LLM with Analytics agent system prompt."""
    system_prompt = ANALYTICS_SYSTEM_PROMPT.format(
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
            tools=ANALYTICS_TOOLS,
            tool_choice="auto",
        )
    except Exception as exc:
        logger.exception("Analytics Agent LLM call failed")
        return {"error": str(exc), "messages": [], "tool_round": state.get("tool_round", 0)}

    choice = response.choices[0]
    msg = choice.message

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


def analytics_route(state: AnalyticsAgentState) -> str:
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


async def analytics_run_tools(state: AnalyticsAgentState) -> dict:
    """Execute Analytics tools."""
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

        logger.info("Analytics tool: %s(%s)", name, json.dumps(args))

        if name == "generate_report":
            channels = args.get("channels", ["all"])
            result_text = (
                f"Report generated ({args.get('report_type', 'weekly')}):\n"
                f"Period: {args.get('period', 'current')}\n"
                f"Channels: {', '.join(channels)}\n"
                f"[Report data would be populated from workspace metrics]"
            )
        elif name == "track_metric":
            result_text = (
                f"Metric tracked: {args.get('metric_name', 'N/A')}\n"
                f"Current: {args.get('current_value', 'N/A')}\n"
                f"Previous: {args.get('previous_value', 'N/A')}\n"
                f"Channel: {args.get('channel', 'N/A')}"
            )
        elif name == "detect_anomaly":
            result_text = (
                f"Anomaly detected ({args.get('severity', 'medium')}):\n"
                f"Metric: {args.get('metric', 'N/A')}\n"
                f"Description: {args.get('description', 'N/A')}\n"
                f"Action: {args.get('suggested_action', 'Review recommended')}"
            )
        elif name == "report_to_ceo":
            result_text = (
                f"Report sent to CEO ({args.get('report_type', 'insight')}):\n"
                f"{args.get('content', 'N/A')[:200]}"
            )
        else:
            result_text = f"Unknown Analytics tool: {name}"

        results.append({"role": "tool", "tool_call_id": tc.get("id", ""), "content": result_text})

    return {"messages": results, "tool_round": state.get("tool_round", 0) + 1}


async def analytics_finalize(state: AnalyticsAgentState) -> dict:
    messages = state.get("messages", [])
    for msg in reversed(messages):
        if isinstance(msg, dict) and msg.get("role") == "assistant" and msg.get("content"):
            return {"final_output": msg["content"]}

    if state.get("error"):
        return {"final_output": f"Analytics Agent error: {state['error'][:200]}"}
    return {"final_output": "Analytics Agent analysis complete."}


# ── Build Graph ───────────────────────────────────────────────────────────────


def build_analytics_graph() -> StateGraph:
    workflow = StateGraph(AnalyticsAgentState)
    workflow.add_node("call_llm", analytics_call_llm)
    workflow.add_node("run_tools", analytics_run_tools)
    workflow.add_node("finalize", analytics_finalize)
    workflow.set_entry_point("call_llm")
    workflow.add_conditional_edges("call_llm", analytics_route, {
        "run_tools": "run_tools", "finalize": "finalize",
    })
    workflow.add_edge("run_tools", "call_llm")
    workflow.add_edge("finalize", END)
    return workflow.compile(checkpointer=MemorySaver())


# ── Agent Class ───────────────────────────────────────────────────────────────


class AnalyticsAgent:
    """Analytics Agent for a specific workspace."""

    def __init__(self, workspace_name: str = "Default", client_name: str = "Client"):
        self.graph = build_analytics_graph()
        self.workspace_name = workspace_name
        self.client_name = client_name
        self._thread_id = f"analytics_{workspace_name}"

    async def chat(self, message: str) -> tuple[str, str]:
        """Chat with Analytics agent. Returns (response, thread_id)."""
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
            logger.exception("Analytics Agent execution failed")
            return "Analytics Agent temporarily unavailable.", self._thread_id

        return result.get("final_output", "Analytics Agent analysis complete."), self._thread_id
