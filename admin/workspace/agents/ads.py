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
from admin.agency.agent_persistence import get_checkpointer
from admin.config import settings
from admin.tools.ads_tools import ADS_TOOLS, execute_ads_tool
from admin.workspace.agent_bus import send_message

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

## Your 20 Tools
### Strategy
- campaign_strategy: Create full campaign strategy with 3 phases
- audience_research: Research target audiences by industry/product/platform
- budget_planner: Allocate budget across prospecting/retargeting/testing
- competitor_ads: Analyze competitor ad strategies
- platform_selection: Recommend platforms per client

### Content
- ad_copy_generator: Generate ad copy with hook formulas
- creative_brief: Create detailed creative brief for Content Agent
- ad_variations: Create A/B test variants
- landing_page_strategy: Plan landing page and tracking
- ad_hashtag_tags: Generate hashtags and UTM tags

### Targeting
- audience_builder: Build audiences with interests/behaviors
- lookalike_audience: Create LAL from converters
- retargeting_setup: Full funnel retargeting
- exclusion_list: Build exclusion audiences

### Optimization
- performance_analyzer: Analyze metrics and detect issues
- auto_optimize: Rule-based auto-optimization
- ab_test_setup: Configure A/B tests

### Reporting
- campaign_report: Generate comprehensive campaign report
- roas_calculator: Calculate ROAS with gap analysis
- creative_score: Score creative effectiveness (0-100)

## Your Jcode Skills (use when needed)
- ads: Full paid ads playbook (Meta Andromeda era, retargeting frameworks)
- copywriting: PAS/BAB frameworks, hook formulas for ad copy
- analytics: Conversion tracking, GA4, pixel setup
- landing-page-copywriter: Landing page copy that converts
- marketing-council: Multi-expert marketing consultation

## Key Playbooks You Know
- Meta Andromeda (2026+): Statics > video, broad targeting + specific creative, identity-trigger keywords
- 4-Component Retargeting: Objection-handling + proof carousel + other-offers + value-first audit
- Headline Mirror Trick: 20-40 headline variants → mirror winner on landing page → 15-20% lift
- Zombie Campaigns: Resurrect dead variants in separate ad sets
- Net Cash > ROAS: Scale until break-even ceiling

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

        # Use real tool executor from ads_tools.py
        tool_result = execute_ads_tool(name, args)
        result_text = json.dumps(tool_result, indent=2, default=str)

        results.append({"role": "tool", "tool_call_id": tc.get("id", ""), "content": result_text})
    return {"messages": results, "tool_round": state.get("tool_round", 0) + 1}


async def ads_finalize(state: AdsAgentState) -> dict:
    for msg in reversed(state.get("messages", [])):
        if isinstance(msg, dict) and msg.get("role") == "assistant" and msg.get("content"):
            return {"final_output": msg["content"]}
    if state.get("error"):
        return {"final_output": f"Ads Agent error: {state['error'][:200]}"}
    return {"final_output": "Ads Agent analysis complete."}


def build_ads_graph(checkpointer=None) -> StateGraph:
    workflow = StateGraph(AdsAgentState)
    workflow.add_node("call_llm", ads_call_llm)
    workflow.add_node("run_tools", ads_run_tools)
    workflow.add_node("finalize", ads_finalize)
    workflow.set_entry_point("call_llm")
    workflow.add_conditional_edges("call_llm", ads_route, {"run_tools": "run_tools", "finalize": "finalize"})
    workflow.add_edge("run_tools", "call_llm")
    workflow.add_edge("finalize", END)
    return workflow.compile(checkpointer=checkpointer or MemorySaver())


class AdsAgent:
    """Ads Agent for a specific workspace."""

    def __init__(self, workspace_name: str = "Default", client_name: str = "Client"):
        self.graph = build_ads_graph(get_checkpointer(self.workspace_name, "ads"))
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

    def request_content(
        self,
        content_type: str,
        topic: str,
        platform: str = "facebook",
        description: str = "",
        style: str = "bold",
        priority: str = "normal",
        quantity: int = 1,
        objective: str = "lead_generation",
        target_audience: dict[str, Any] | None = None,
        emotional_hook: str = "fear",
        cta: str = "sign_up",
        key_message: str = "",
        competitor_context: str = "",
        constraints: str = "",
        copy_text: str = "",
    ) -> dict[str, Any]:
        """Request ad creatives from Content Agent with DEEP brief.

        Ads Agent samajhta hai ki ad creative sirf image nahi hai —
        yeh CONVERSION ka tool hai. Isliye brief mein sab kuch deta hai:
        - Kya banana hai (content_type)
        - Kahan dikhega (platform)
        - Kisko dikhana hai (target_audience)
        - Kya feel karna hai (emotional_hook)
        - Kya karna hai (cta)
        - Kyun behtar hai (competitor_context)
        """
        from admin.workspace.agents.brief_builder import build_domain_brief, brief_to_text

        brief = build_domain_brief(
            domain="ads",
            content_type=content_type,
            topic=topic,
            platform=platform,
            description=description,
            style=style,
            priority=priority,
            quantity=quantity,
            objective=objective,
            target_audience=target_audience,
            emotional_hook=emotional_hook,
            cta=cta,
            key_message=key_message,
            competitor_context=competitor_context,
            constraints=constraints,
            copy_text=copy_text,
        )

        brief_content = brief_to_text(brief)

        try:
            send_message(
                from_agent="ads",
                to_agent="content",
                workspace_id=self.workspace_name,
                subject=f"Ads needs {content_type}: {topic[:50]}",
                content=brief_content,
                message_type="brief",
                metadata=brief,
            )
            logger.info(
                "Ads Agent requested content: %s (%s) x%d | objective=%s, hook=%s",
                content_type, topic[:50], quantity, objective, emotional_hook,
            )
            return {"status": "brief_sent", "brief": brief}
        except Exception as e:
            logger.warning("Failed to request content: %s", e)
            return {"status": "error", "error": str(e)}
