"""Website Agent — Full pipeline: design, development, hosting, maintenance.

Domain (from interview Q1-Q6):
- Full pipeline: Layout Design → Development → Domain/Hosting → Deploy
- Agent decides tech stack (WordPress, Next.js, Webflow, etc.)
- CEO approval before implementation
- 24/7 monitoring (broken links, performance, security, uptime)
- Client may provide own domain/hosting
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

WEBSITE_SYSTEM_PROMPT = """You are the Website Agent for workspace '{workspace_name}' (client: {client_name}).

You are a full-stack web developer and designer.

## Your Expertise
- Web design (layout, UI/UX, responsive design)
- Frontend development (Next.js, React, HTML/CSS/JS)
- CMS platforms (WordPress, Webflow, Shopify)
- Domain registration and hosting setup
- Deployment (Vercel by default for frontend)
- Site maintenance and monitoring

## Your Rules (from interview)
1. You design AND build — full pipeline ownership
2. You decide the tech stack per client, considering client preferences
3. You propose designs to CEO → CEO approves → you implement
4. You monitor sites 24/7 — broken links, performance, security, uptime
5. Client may provide their own domain/hosting — you adapt
6. Frontend hosting defaults to Vercel
7. CEO can override your tech stack choice anytime

## Tech Stack Decision Framework
- Simple landing page → Next.js + Vercel
- E-commerce → Shopify or Next.js + Stripe
- Content-heavy blog → WordPress or Next.js + CMS
- Client existing platform → adapt to their stack

## What you know about this workspace

{workspace_context}

## Thinking Process
1. What does the client need (landing page, full site, e-commerce)?
2. What tech stack fits best?
3. What's the design approach?
4. What's the timeline?
5. What's my specific plan?
"""


WEBSITE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "propose_design",
            "description": "Propose a website design/layout plan to CEO for approval.",
            "parameters": {
                "type": "object",
                "properties": {
                    "page_type": {"type": "string", "description": "Type of page/site"},
                    "tech_stack": {"type": "string", "description": "Proposed tech stack"},
                    "design_plan": {"type": "string", "description": "Design and layout plan"},
                    "timeline": {"type": "string", "description": "Estimated timeline"},
                },
                "required": ["page_type", "tech_stack", "design_plan"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "report_to_ceo",
            "description": "Report site status or issue to CEO.",
            "parameters": {
                "type": "object",
                "properties": {
                    "report_type": {"type": "string", "enum": ["design_proposal", "progress_update", "site_alert"]},
                    "content": {"type": "string"},
                },
                "required": ["report_type", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_site_health",
            "description": "Run a site health check (performance, broken links, security).",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Site URL to check"},
                    "check_type": {"type": "string", "enum": ["full", "performance", "security", "links"]},
                },
                "required": ["url"],
            },
        },
    },
]


class WebsiteAgentState(TypedDict):
    messages: Annotated[list[dict[str, Any]], lambda e, n: e + n]
    workspace_name: str
    client_name: str
    workspace_context: str
    tool_round: int
    final_output: str
    error: str | None


async def website_call_llm(state: WebsiteAgentState) -> dict:
    system_prompt = WEBSITE_SYSTEM_PROMPT.format(
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
        response = await client_api.chat.completions.create(model=settings.WORKSPACE_AGENT_MODEL, messages=messages, tools=WEBSITE_TOOLS, tool_choice="auto")
    except Exception as exc:
        logger.exception("Website Agent LLM call failed")
        return {"error": str(exc), "messages": [], "tool_round": state.get("tool_round", 0)}

    msg = response.choices[0].message
    assistant_msg: dict[str, Any] = {"role": "assistant", "content": msg.content or ""}
    if msg.tool_calls:
        assistant_msg["tool_calls"] = [{"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}} for tc in msg.tool_calls]
    return {"messages": [assistant_msg], "error": None}


def website_route(state: WebsiteAgentState) -> str:
    if state.get("error"):
        return "finalize"
    last = state.get("messages", [{}])[-1]
    if isinstance(last, dict) and last.get("tool_calls"):
        return "run_tools" if state.get("tool_round", 0) < MAX_TOOL_ROUNDS else "finalize"
    return "finalize"


async def website_run_tools(state: WebsiteAgentState) -> dict:
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

        if name == "propose_design":
            result_text = f"Design proposal submitted:\nType: {args.get('page_type', 'N/A')}\nTech: {args.get('tech_stack', 'N/A')}\nPlan: {args.get('design_plan', 'N/A')[:200]}\nTimeline: {args.get('timeline', 'TBD')}"
        elif name == "report_to_ceo":
            result_text = f"Report sent to CEO ({args.get('report_type', 'N/A')}):\n{args.get('content', 'N/A')[:200]}"
        elif name == "check_site_health":
            result_text = f"Site health check for {args.get('url', 'N/A')} ({args.get('check_type', 'full')}):\n[Health check results would appear here]"
        else:
            result_text = f"Unknown tool: {name}"
        results.append({"role": "tool", "tool_call_id": tc.get("id", ""), "content": result_text})
    return {"messages": results, "tool_round": state.get("tool_round", 0) + 1}


async def website_finalize(state: WebsiteAgentState) -> dict:
    for msg in reversed(state.get("messages", [])):
        if isinstance(msg, dict) and msg.get("role") == "assistant" and msg.get("content"):
            return {"final_output": msg["content"]}
    if state.get("error"):
        return {"final_output": f"Website Agent error: {state['error'][:200]}"}
    return {"final_output": "Website Agent analysis complete."}


def build_website_graph() -> StateGraph:
    workflow = StateGraph(WebsiteAgentState)
    workflow.add_node("call_llm", website_call_llm)
    workflow.add_node("run_tools", website_run_tools)
    workflow.add_node("finalize", website_finalize)
    workflow.set_entry_point("call_llm")
    workflow.add_conditional_edges("call_llm", website_route, {"run_tools": "run_tools", "finalize": "finalize"})
    workflow.add_edge("run_tools", "call_llm")
    workflow.add_edge("finalize", END)
    return workflow.compile(checkpointer=MemorySaver())


class WebsiteAgent:
    def __init__(self, workspace_name: str = "Default", client_name: str = "Client"):
        self.graph = build_website_graph()
        self.workspace_name = workspace_name
        self.client_name = client_name
        self._thread_id = f"website_{workspace_name}"

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
            logger.exception("Website Agent execution failed")
            return "Website Agent temporarily unavailable.", self._thread_id
        return result.get("final_output", "Website Agent analysis complete."), self._thread_id

    def request_content(
        self,
        content_type: str,
        topic: str,
        platform: str = "website",
        description: str = "",
        style: str = "professional",
        priority: str = "normal",
    ) -> dict[str, Any]:
        """Request website content from Content Agent via agent_bus.

        Website Agent uses this when it needs hero images, banners,
        icons, landing page visuals, or any visual content for the website.

        Flow:
        1. Website Agent sends brief to Content Agent via agent_bus
        2. Content Agent enhances brief with brand intelligence
        3. Content Agent queues job for GPU processing
        4. On completion, Content Agent notifies Website Agent back
        """
        brief_content = (
            f"Website Content Request:\n"
            f"- Type: {content_type}\n"
            f"- Topic: {topic}\n"
            f"- Platform: {platform}\n"
            f"- Description: {description}\n"
            f"- Style: {style}\n"
            f"- Priority: {priority}"
        )

        try:
            send_message(
                from_agent="website",
                to_agent="content",
                workspace_id=self.workspace_name,
                subject=f"Website needs {content_type}: {topic[:50]}",
                content=brief_content,
                message_type="brief",
                metadata={
                    "content_type": content_type,
                    "platform": platform,
                    "style": style,
                    "priority": priority,
                },
            )
            logger.info(
                "Website Agent requested content from Content Agent: %s (%s)",
                content_type, topic[:50],
            )
            return {"status": "brief_sent", "content_type": content_type, "topic": topic}
        except Exception as e:
            logger.warning("Failed to request content from Content Agent: %s", e)
            return {"status": "error", "error": str(e)}
