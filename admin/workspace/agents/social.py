"""Social Agent — Social media strategist (Instagram, LinkedIn, X).

Domain (from interview Q1-Q3):
- STRATEGIST only, not executor (creates strategy, not posts)
- Platforms: Instagram + LinkedIn + X (agent decides per client)
- Content calendar, posting schedule, engagement plan, content themes, growth tactics
- Organic-first, then paid/influencer based on client goals
- Briefs Content Agent for visual content
"""

from __future__ import annotations

import json
import logging
from typing import Annotated, Any, TypedDict

import openai
from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from admin.config import settings
from admin.workspace.agent_bus import send_message

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 5

SOCIAL_SYSTEM_PROMPT = """You are the Social Media Agent for workspace '{workspace_name}' (client: {client_name}).

You are a social media STRATEGIST — you create the strategy, not the actual posts.

## Your Expertise
- Platform strategy (Instagram, LinkedIn, X/Twitter)
- Content calendars and posting schedules
- Hashtag research and trending topics
- Community engagement strategies
- Organic growth tactics
- Content themes and brand voice guidelines
- Audience analysis and growth planning

## Your Rules (from interview)
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
- Hashtag strategy
- Engagement plan (community management)
- Growth tactics (follower acquisition)
- Platform-specific strategy notes

## What you know about this workspace

{workspace_context}

## Thinking Process
1. What platforms fit this client best?
2. What's the target audience on each platform?
3. What content themes resonate?
4. What's the posting cadence?
5. What's my 30-day strategy?
"""


SOCIAL_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_content_calendar",
            "description": "Create a content calendar for social media.",
            "parameters": {
                "type": "object",
                "properties": {
                    "platform": {"type": "string", "description": "Target platform"},
                    "duration": {"type": "string", "description": "Calendar duration (1 week, 1 month)"},
                    "themes": {"type": "string", "description": "Content themes"},
                },
                "required": ["platform", "duration"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "brief_content_agent",
            "description": "Brief Content Agent for visual social content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "visual_type": {"type": "string", "description": "Type of visual needed"},
                    "brief": {"type": "string", "description": "Creative brief"},
                    "platform": {"type": "string", "description": "Target platform"},
                },
                "required": ["visual_type", "brief"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "report_to_ceo",
            "description": "Report social strategy or performance to CEO.",
            "parameters": {
                "type": "object",
                "properties": {
                    "report_type": {"type": "string", "enum": ["strategy_proposal", "performance_update", "issue_alert"]},
                    "content": {"type": "string"},
                },
                "required": ["report_type", "content"],
            },
        },
    },
]


class SocialAgentState(TypedDict):
    messages: Annotated[list[dict[str, Any]], lambda e, n: e + n]
    workspace_name: str
    client_name: str
    workspace_context: str
    tool_round: int
    final_output: str
    error: str | None


async def social_call_llm(state: SocialAgentState) -> dict:
    system_prompt = SOCIAL_SYSTEM_PROMPT.format(
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
        client_api = openai.AsyncOpenAI(api_key=settings.WORKSPACE_API_KEY or None, base_url=settings.WORKSPACE_API_BASE or None)
        response = await client_api.chat.completions.create(model=settings.WORKSPACE_AGENT_MODEL, messages=messages, tools=SOCIAL_TOOLS, tool_choice="auto")
    except Exception as exc:
        logger.exception("Social Agent LLM call failed")
        return {"error": str(exc), "messages": [], "tool_round": state.get("tool_round", 0)}

    msg = response.choices[0].message
    assistant_msg: dict[str, Any] = {"role": "assistant", "content": msg.content or ""}
    if msg.tool_calls:
        assistant_msg["tool_calls"] = [{"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}} for tc in msg.tool_calls]
    return {"messages": [assistant_msg], "error": None}


def social_route(state: SocialAgentState) -> str:
    if state.get("error"):
        return "finalize"
    last = state.get("messages", [{}])[-1]
    if isinstance(last, dict) and last.get("tool_calls"):
        return "run_tools" if state.get("tool_round", 0) < MAX_TOOL_ROUNDS else "finalize"
    return "finalize"


async def social_run_tools(state: SocialAgentState) -> dict:
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
        if name == "create_content_calendar":
            result_text = f"Content calendar created for {args.get('platform', 'N/A')} ({args.get('duration', 'N/A')}):\nThemes: {args.get('themes', 'TBD')}\n[Detailed calendar would appear here]"
        elif name == "brief_content_agent":
            result_text = f"Visual brief sent to Content Agent:\nType: {args.get('visual_type', 'N/A')}\nBrief: {args.get('brief', 'N/A')[:200]}"
        elif name == "report_to_ceo":
            result_text = f"Report sent to CEO ({args.get('report_type', 'N/A')}):\n{args.get('content', 'N/A')[:200]}"
        else:
            result_text = f"Unknown tool: {name}"
        results.append({"role": "tool", "tool_call_id": tc.get("id", ""), "content": result_text})
    return {"messages": results, "tool_round": state.get("tool_round", 0) + 1}


async def social_finalize(state: SocialAgentState) -> dict:
    for msg in reversed(state.get("messages", [])):
        if isinstance(msg, dict) and msg.get("role") == "assistant" and msg.get("content"):
            return {"final_output": msg["content"]}
    if state.get("error"):
        return {"final_output": f"Social Agent error: {state['error'][:200]}"}
    return {"final_output": "Social Agent analysis complete."}


def build_social_graph() -> StateGraph:
    workflow = StateGraph(SocialAgentState)
    workflow.add_node("call_llm", social_call_llm)
    workflow.add_node("run_tools", social_run_tools)
    workflow.add_node("finalize", social_finalize)
    workflow.set_entry_point("call_llm")
    workflow.add_conditional_edges("call_llm", social_route, {"run_tools": "run_tools", "finalize": "finalize"})
    workflow.add_edge("run_tools", "call_llm")
    workflow.add_edge("finalize", END)
    return workflow.compile(checkpointer=MemorySaver())


class SocialAgent:
    def __init__(self, workspace_name: str = "Default", client_name: str = "Client"):
        self.graph = build_social_graph()
        self.workspace_name = workspace_name
        self.client_name = client_name
        self._thread_id = f"social_{workspace_name}"

    async def chat(self, message: str) -> tuple[str, str]:
        workspace_context = f"Workspace: {self.workspace_name}, Client: {self.client_name}"
        initial_state = {
            "messages": [{"role": "user", "content": message}],
            "workspace_name": self.workspace_name, "client_name": self.client_name,
            "workspace_context": workspace_context,
            "tool_round": 0, "final_output": "", "error": None,
        }
        try:
            result = await self.graph.ainvoke(initial_state, config={"configurable": {"thread_id": self._thread_id}})
        except Exception:
            logger.exception("Social Agent execution failed")
            return "Social Agent temporarily unavailable.", self._thread_id
        return result.get("final_output", "Social Agent analysis complete."), self._thread_id

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
        """Request social media content from Content Agent via agent_bus.

        Social Agent uses this when it needs social media images,
        reels covers, stories, or any visual content for social platforms.

        Flow:
        1. Social Agent sends brief to Content Agent via agent_bus
        2. Content Agent enhances brief with brand intelligence
        3. Content Agent queues job for GPU processing
        4. On completion, Content Agent notifies Social Agent back
        """
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
                metadata={
                    "content_type": content_type,
                    "platform": platform,
                    "style": style,
                    "quantity": quantity,
                    "priority": priority,
                },
            )
            logger.info(
                "Social Agent requested content from Content Agent: %s (%s) x%d",
                content_type, topic[:50], quantity,
            )
            return {"status": "brief_sent", "content_type": content_type, "topic": topic, "quantity": quantity}
        except Exception as e:
            logger.warning("Failed to request content from Content Agent: %s", e)
            return {"status": "error", "error": str(e)}
