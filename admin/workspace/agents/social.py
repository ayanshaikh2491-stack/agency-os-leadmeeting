"""Social Agent — Social media strategist with real tools.

Real tools (10):
1. content_calendar — Generate content calendar
2. hashtag_research — Find relevant hashtags
3. posting_schedule — Best times to post
4. competitor_analysis — Analyze competitor social presence
5. trend_research — Find trending topics
6. engagement_strategy — Plan community management
7. platform_strategy — Platform-specific strategy
8. content_gap_analysis — What competitors post that you don't
9. audience_analysis — Target audience insights
10. growth_tactics — Follower acquisition plan

Interview Q1-Q3:
- STRATEGIST only, not executor (creates strategy, not posts)
- Platforms: Instagram + LinkedIn + X (agent decides per client)
- Content calendar, posting schedule, engagement plan, growth tactics
- Organic-first, then paid/influencer
- Briefs Content Agent for visual content

LangGraph: call_llm -> route -> (run_tools | finalize) -> END
"""
from __future__ import annotations

import json
import logging
from typing import Annotated, Any, TypedDict

import openai
from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from admin.config import settings
from admin.tools.social_tools import SOCIAL_TOOLS, execute_social_tool
from admin.workspace.agent_bus import send_message

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 8


# ── System Prompt ────────────────────────────────────────────────────────────

SOCIAL_SYSTEM_PROMPT = """You are the Social Media Agent for workspace '{workspace_name}' (client: {client_name}).

You are a social media STRATEGIST. You create strategy, not the actual posts.

## Your Expertise
- Platform strategy (Instagram, LinkedIn, X/Twitter, Facebook, TikTok)
- Content calendars and posting schedules
- Hashtag research and trending topics
- Community engagement strategies
- Organic growth tactics
- Content themes and brand voice guidelines
- Audience analysis and growth planning
- Competitor analysis

## Your Tools (USE THEM!)
You have 10 real tools. ALWAYS use tools before giving advice.

### Planning Tools
1. **content_calendar(platform, duration, niche, brand_tone)** — Generate content calendar
2. **posting_schedule(platform, timezone_offset, audience)** — Best times to post
3. **platform_strategy(industry, goals, budget)** — Which platforms to prioritize

### Research Tools
4. **hashtag_research(niche, platform, count)** — Find relevant hashtags by tier
5. **trend_research(niche, platform)** — Trending topics and viral formats
6. **competitor_analysis(competitors, platform, niche)** — Analyze competitor presence
7. **content_gap_analysis(your_content, competitor_content, niche)** — Find gaps

### Growth Tools
8. **engagement_strategy(platform, goals, audience_size)** — Community management plan
9. **audience_analysis(industry, platform, location)** — Target audience insights
10. **growth_tactics(current_followers, platform, niche, budget)** — Follower acquisition

## Your Rules (from interview Q1-Q3)
1. You are a STRATEGIST — you create strategy, content calendars, engagement plans
2. You do NOT create visual content — brief Content Agent for that
3. You DO create text content — captions, hashtags, engagement copy
4. Organic-first approach — start with organic growth, add paid later
5. You decide which platforms to activate per client based on their industry/goals
6. Your primary goal: strategy + execution plan must be solid and measurable
7. CEO can override your strategy anytime

## Strategy Deliverables
- Content calendar (weekly/monthly)
- Posting schedule (best times per platform)
- Content themes (what to post about)
- Hashtag strategy (tiered by volume)
- Engagement plan (community management)
- Growth tactics (follower acquisition)
- Platform-specific strategy notes

## Workflow
1. When asked for strategy -> use platform_strategy + content_calendar
2. When asked about hashtags -> use hashtag_research
3. When asked about posting times -> use posting_schedule
4. When asked about competitors -> use competitor_analysis
5. When asked about growth -> use growth_tactics + engagement_strategy
6. When asked about audience -> use audience_analysis
7. When you need visuals -> brief Content Agent with detailed brief

## Briefing Content Agent
When you need visual content, provide a DETAILED brief:
- Post type (carousel, reel, story, single image)
- Topic and description
- Mood and style
- Target audience
- Platform and dimensions
- Text overlay or CTA
- Why this content works

## Behavioural rules
- Be strategic and data-driven. Give specific numbers, schedules, tactics.
- Think about ROI — every strategy should have measurable goals.
- Consider the client's industry, audience, and resources.
- Start with what's achievable, then scale.
- Never refuse a task — if you can't do something, explain why and suggest alternatives.
"""


# ── State ─────────────────────────────────────────────────────────────────────

class SocialAgentState(TypedDict):
    messages: Annotated[list[dict[str, Any]], "Conversation"]
    workspace_name: str
    client_name: str
    tool_round: int
    final_output: str
    error: str | None


# ── Helpers ──────────────────────────────────────────────────────────────────

def _get_llm_client() -> openai.OpenAI:
    api_key = settings.WORKSPACE_API_KEY or settings.AGENCY_CEO_API_KEY or "dummy"
    base_url = settings.WORKSPACE_API_BASE or settings.AGENCY_CEO_API_BASE or None
    return openai.OpenAI(api_key=api_key, base_url=base_url) if base_url else openai.OpenAI(api_key=api_key)


# ── Graph Nodes ──────────────────────────────────────────────────────────────

async def social_call_llm(state: SocialAgentState) -> dict[str, Any]:
    """Call the LLM with tools."""
    system = SOCIAL_SYSTEM_PROMPT.format(
        workspace_name=state.get("workspace_name", "Default"),
        client_name=state.get("client_name", "Client"),
    )
    messages = [{"role": "system", "content": system}]
    messages.extend(state.get("messages", []))

    client = _get_llm_client()
    model = settings.WORKSPACE_AGENT_MODEL or "llama-3.3-70b-versatile"

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=SOCIAL_TOOLS,
            tool_choice="auto",
            temperature=0.3,
            max_tokens=4096,
        )
    except Exception as e:
        logger.exception("Social Agent LLM call failed")
        return {"error": f"LLM call failed: {str(e)[:200]}"}

    choice = response.choices[0]
    content = choice.message.content or ""
    tool_calls = choice.message.tool_calls or []

    new_messages = []

    if tool_calls:
        new_messages.append({
            "role": "assistant",
            "content": content,
            "tool_calls": [
                {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in tool_calls
            ],
        })

        for tc in tool_calls:
            tool_name = tc.function.name
            try:
                args = json.loads(tc.function.arguments)
            except (json.JSONDecodeError, TypeError):
                args = {}

            logger.info("Social tool call: %s(%s)", tool_name, args)
            result = execute_social_tool(tool_name, args)
            result_str = json.dumps(result, default=str)[:8000]

            new_messages.append({"role": "tool", "tool_call_id": tc.id, "content": result_str})

        return {"messages": new_messages, "error": None}

    # No tool calls — final response
    new_messages.append({"role": "assistant", "content": content})
    return {"messages": new_messages, "final_output": content, "error": None}


def social_route(state: SocialAgentState) -> str:
    """Route: tool_calls -> loop, no calls -> finalize."""
    if state.get("error"):
        return "finalize"
    if state.get("tool_round", 0) >= MAX_TOOL_ROUNDS:
        return "finalize"

    msgs = state.get("messages", [])
    if not msgs:
        return "finalize"

    last = msgs[-1]
    if isinstance(last, dict) and last.get("tool_calls"):
        return "run_tools"

    return "finalize"


async def social_run_tools(state: SocialAgentState) -> dict[str, Any]:
    """Execute tools from last message."""
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

        logger.info("Social tool: %s(%s)", name, args)
        result = execute_social_tool(name, args)
        result_str = json.dumps(result, default=str)[:8000]

        results.append({"role": "tool", "tool_call_id": tc.get("id", ""), "content": result_str})

    return {"messages": results, "tool_round": state.get("tool_round", 0) + 1}


def social_finalize(state: SocialAgentState) -> dict[str, Any]:
    """Extract final output."""
    output = state.get("final_output", "")
    if output:
        return {"final_output": output}

    for msg in reversed(state.get("messages", [])):
        if isinstance(msg, dict) and msg.get("role") == "assistant" and msg.get("content"):
            return {"final_output": msg["content"]}

    if state.get("error"):
        return {"final_output": f"Social Agent error: {state['error'][:200]}"}

    return {"final_output": "Social Agent analysis complete."}


# ── Graph ────────────────────────────────────────────────────────────────────

def build_social_graph() -> StateGraph:
    graph = StateGraph(SocialAgentState)
    graph.add_node("call_llm", social_call_llm)
    graph.add_node("run_tools", social_run_tools)
    graph.add_node("finalize", social_finalize)
    graph.set_entry_point("call_llm")
    graph.add_conditional_edges("call_llm", social_route, {
        "run_tools": "run_tools",
        "finalize": "finalize",
    })
    graph.add_edge("run_tools", "call_llm")
    graph.add_edge("finalize", END)
    return graph.compile(checkpointer=MemorySaver())


_graph = None

def get_social_graph() -> StateGraph:
    global _graph
    if _graph is None:
        _graph = build_social_graph()
    return _graph


# ── SocialAgent Class ──────────────────────────────────────────────────────

class SocialAgent:
    """Social Media Strategist with real tools."""

    def __init__(self, workspace_name: str = "Default", client_name: str = "Client"):
        self.workspace_name = workspace_name
        self.client_name = client_name
        self._thread_id = f"social_{workspace_name}"
        self._graph = get_social_graph()

    async def chat(self, message: str) -> tuple[str, str]:
        """Process a social media request."""
        initial_state: dict[str, Any] = {
            "messages": [{"role": "user", "content": message}],
            "workspace_name": self.workspace_name,
            "client_name": self.client_name,
            "tool_round": 0,
            "final_output": "",
            "error": None,
        }

        try:
            result = self._graph.invoke(
                initial_state,
                config={"configurable": {"thread_id": self._thread_id}},
            )
            return result.get("final_output", "Social Agent analysis complete."), self._thread_id
        except Exception:
            logger.exception("Social Agent execution failed")
            return "Social Agent temporarily unavailable.", self._thread_id

    def request_content(
        self,
        content_type: str,
        topic: str,
        platform: str = "instagram",
        description: str = "",
        style: str = "bold",
        priority: str = "normal",
        quantity: int = 1,
    ) -> dict[str, Any]:
        """Request visual content from Content Agent via agent_bus."""
        brief_content = (
            f"Social Content Request:\n"
            f"- Type: {content_type}\n"
            f"- Topic: {topic}\n"
            f"- Platform: {platform}\n"
            f"- Description: {description}\n"
            f"- Style: {style}\n"
            f"- Quantity: {quantity}\n"
            f"- Priority: {priority}"
        )

        try:
            send_message(
                from_agent="social",
                to_agent="content",
                workspace_id=self.workspace_name,
                subject=f"Social needs {content_type}: {topic[:50]}",
                content=brief_content,
                message_type="brief",
                metadata={"content_type": content_type, "platform": platform, "style": style, "quantity": quantity, "priority": priority},
            )
            return {"status": "brief_sent", "content_type": content_type, "topic": topic, "quantity": quantity}
        except Exception as e:
            return {"status": "error", "error": str(e)}
