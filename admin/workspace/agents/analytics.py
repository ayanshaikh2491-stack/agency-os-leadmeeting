"""Analytics Agent — Performance tracking, reporting, data visualization.

Domain (from interview):
- Track client performance metrics (SEO rankings, ad ROAS, social engagement, website traffic)
- Generate weekly/monthly reports
- Data-driven insights and recommendations
- Cross-channel analytics (combine SEO + Ads + Social data)
- Automated monitoring with alerts
- Email reports to agency owner, CEO, and client
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
from admin.tools.analytics_tools import ANALYTICS_TOOLS, execute_analytics_tool
from admin.workspace.agent_bus import send_message

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 5


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
- Email reports to agency owner, CEO, and client

## Your Rules (from interview)
1. You track ALL channels — SEO, Ads, Social, Website — in one dashboard
2. You generate automated weekly/monthly reports
3. You alert CEO on anomalies (traffic drops, ranking losses, ad spend spikes)
4. You provide data-driven recommendations, not just numbers
5. You learn from historical data — identify trends over time
6. You can pull data from any agent's output for cross-channel analysis
7. CEO can request custom reports anytime
8. You send email reports to: agency owner, workspace CEO, and client

## Your 20 Tools
### Reporting
- weekly_report: Generate weekly performance report
- monthly_report: Comprehensive monthly report with trends
- campaign_report: Detailed campaign performance report
- custom_report: Custom report based on focus areas

### Tracking
- track_traffic: Track website traffic metrics
- track_rankings: Track keyword rankings
- track_conversions: Track conversion metrics
- track_revenue: Track revenue and profitability

### Analysis
- cross_channel_analysis: Analyze all channels together
- roi_calculator: Calculate ROI per channel
- funnel_analysis: Analyze conversion funnel
- competitor_benchmark: Benchmark against competitors

### Alerts
- anomaly_detector: Detect metric anomalies
- threshold_alert: Check thresholds and alert
- competitor_alert: Alert on competitor activity

### Forecasting
- traffic_forecast: Forecast traffic growth
- budget_forecast: Forecast budget needs
- growth_projection: Project growth to targets

### Data
- data_aggregator: Aggregate all channel data
- email_report: Send report via email

## Email Reports
When generating reports, use email_report tool to send to:
- Agency owner email
- Workspace CEO email
- Client email

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


class AnalyticsAgentState(TypedDict):
    messages: Annotated[list[dict[str, Any]], lambda e, n: e + n]
    workspace_name: str
    client_name: str
    workspace_context: str
    tool_round: int
    final_output: str
    error: str | None


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
    """Execute Analytics tools using real tool executor."""
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

        # Use real tool executor from analytics_tools.py
        tool_result = execute_analytics_tool(name, args)
        result_text = json.dumps(tool_result, indent=2, default=str)

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


def build_analytics_graph(checkpointer=None) -> StateGraph:
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
    return workflow.compile(checkpointer=checkpointer or MemorySaver())


class AnalyticsAgent:
    """Analytics Agent for a specific workspace."""

    def __init__(self, workspace_name: str = "Default", client_name: str = "Client"):
        self.graph = build_analytics_graph(get_checkpointer(self.workspace_name, "analytics"))
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

    def send_report_email(
        self,
        to: list[str],
        report_type: str = "weekly",
        custom_message: str = "",
    ) -> dict[str, Any]:
        """Send analytics report via email.

        Sends to: agency owner, workspace CEO, and client.
        """
        from admin.utils.email_sender import send_report_email
        from admin.tools.analytics_tools import weekly_report, monthly_report

        # Generate report
        if report_type == "monthly":
            report = monthly_report(self.workspace_name, self.client_name)
        else:
            report = weekly_report(self.workspace_name, self.client_name)

        # Build email body
        body_lines = [
            f"📊 {report_type.title()} Report — {self.workspace_name}",
            f"Client: {self.client_name}",
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
        ]

        if "summary" in report:
            s = report["summary"]
            body_lines.extend([
                "Summary:",
                f"  Traffic: {s.get('total_traffic', 'N/A'):,}",
                f"  Leads: {s.get('total_leads', 'N/A')}",
                f"  Revenue: ₹{s.get('total_revenue', 0):,}",
                f"  Spend: ₹{s.get('total_spend', 0):,}",
                f"  ROAS: {s.get('overall_roas', 'N/A')}x",
                "",
            ])

        if report.get("action_items"):
            body_lines.append("Action Items:")
            for item in report["action_items"]:
                body_lines.append(f"  • {item}")

        if custom_message:
            body_lines.extend(["", "Note:", f"  {custom_message}"])

        body = "\n".join(body_lines)

        result = send_report_email(
            to=to,
            report_title=f"{report_type.title()} Report — {self.client_name}",
            report_body=body,
            workspace_name=self.workspace_name,
            client_name=self.client_name,
            report_type=report_type,
        )

        return {
            "status": result.get("status", "unknown"),
            "report_type": report_type,
            "recipients": to,
            "email_result": result,
        }

    def report_to_ceo(
        self,
        report_type: str = "insight",
        content: str = "",
    ) -> dict[str, Any]:
        """Send analytics insight/alert to CEO via agent_bus."""
        try:
            send_message(
                from_agent="analytics",
                to_agent="ceo",
                workspace_id=self.workspace_name,
                subject=f"Analytics {report_type}: {self.client_name}",
                content=content,
                message_type="report",
                metadata={"report_type": report_type},
            )
            return {"status": "sent", "to": "ceo", "report_type": report_type}
        except Exception as e:
            return {"status": "error", "error": str(e)}
