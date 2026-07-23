"""Content Agent — Visual + Text Execution Engine.

Interview Q1: Creates images, videos, AND text content (blog, copy, strategy).
Interview Q2: Full visual spectrum — social graphics, ad creatives, videos, reels, infographics.
Interview Q3: Kaggle API — FLUX for images, CogVideo for videos (API-driven, free GPU).
Interview Q4: Per-workspace isolation — each workspace has its own Content Agent.
Interview Q5: Brand discovery — auto-discovers client brand from social media/website.
Interview Q6: Domain agent owns approval — briefs from SEO, Ads, Social, Website.
Interview Q7: Cross-project learning — reports to workspace CEO, shares with Agency Content Agent.

Architecture (follows SEO agent LangGraph pattern):
  call_llm -> route_from_llm -> (call_llm loop | finalize -> END)

Tool execution happens INSIDE call_llm (same pattern as SEO agent).
No separate run_tools node needed.

Dual Reporting (Interview Q7, Q24, Q27):
  1. Workspace Content Agent --> Domain Agent (operational report via agent_bus)
  2. Workspace Content Agent --> Agency Content Agent (cross-project learning)
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
from admin.tools.visual_tools import VISUAL_TOOLS, execute_visual_tool
from admin.tools.kaggle_tools import execute_kaggle_tool
from admin.tools.content_tools import CONTENT_TOOLS, execute_content_tool
from admin.workspace.agent_bus import send_message, share_knowledge
from admin.agency.content_agent import ContentReport, get_agency_content_agent

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 10


# ── Unified Tool Registry ─────────────────────────────────────────────────────

# Merge visual + kaggle + content tools into one unified list for the LLM
ALL_CONTENT_TOOLS = VISUAL_TOOLS + CONTENT_TOOLS


# ── System Prompt ──────────────────────────────────────────────────────────────

CONTENT_SYSTEM_PROMPT = """You are the Content Agent for workspace '{workspace_name}' (client: {client_name}).

You are a FULL-SPECTRUM content execution engine. You create images, videos, AND text content.

## What You Do
1. **Visual Content** — images, social graphics, ad creatives, videos, reels, infographics
2. **Text Content** — blog posts, website copy, ad copy, social captions, meta descriptions
3. **Content Strategy** — content briefs, calendars, gap analysis, competitor research
4. **Brand Discovery** — auto-discover client brand from their website/social media
5. **Content Optimization** — readability analysis, SEO scoring, content rewriting
6. **Social Repurposing** — convert content across platforms (blog -> Instagram, etc.)

## Your Tools

### Brand & Visual Planning
1. **discover_brand_identity(website_url)** — Scan client website for brand: logo, colors, style
2. **parse_visual_brief(brief_text)** — Parse a domain agent's brief to extract visual details
3. **plan_visual_production(brief, brand_identity)** — Create production plan with prompts, dimensions

### Image Generation (Kaggle GPU — FLUX)
4. **generate_image_kaggle(prompt, width, height, steps)** — Generate any AI image via FLUX
5. **generate_ad_image(product, platform, style)** — Ad creative sized for specific platform
6. **generate_social_image(topic, platform)** — Social media post image
7. **generate_hero_image(topic, style)** — Website/blog hero banner
8. **batch_generate_images(topics, platform)** — Multiple images for content calendar

### Video Generation (Kaggle GPU — CogVideoX)
9. **generate_video_kaggle(prompt, frames)** — Generate AI video via CogVideoX
10. **generate_video_ad(product, duration)** — Video advertisement

### Text Content & Strategy
11. **analyze_readability(url)** — Analyze content readability with Flesch-Kincaid scores
12. **generate_content_brief(topic, target_audience, word_count)** — Full content brief with outline
13. **generate_blog_post(topic, keywords, word_count)** — SEO-optimized blog post with HTML
14. **optimize_meta_descriptions(url)** — Analyze and optimize meta tags
15. **rewrite_content(text, style)** — Rewrite for better readability
16. **generate_content_calendar(niche, weeks)** — Weekly content calendar
17. **analyze_content_gaps(url, competitors)** — Find content gaps vs competitors
18. **search_images(query, count)** — Search free stock images (Unsplash)
19. **get_social_image_specs(platform)** — Get exact image sizes per platform
20. **repurpose_for_social(blog_content, platform)** — Convert content across platforms
21. **generate_ad_copy(product, platform)** — Generate ad copy for any platform

## Multi-phase thinking process
Before answering, reason through these phases inside ```think blocks:

### 1. Deconstruct
What does the brief require? Visuals, text, or both? What platforms?

### 2. Brand Check
Do I have brand identity? If not, discover_brand_identity first.

### 3. Plan
What to create? How many items? What tools to use? What GPU time?

### 4. Execute
Use your tools to generate visuals AND/OR text content as needed.

### 5. Deliver
Present results — what was created, file locations, completion status.

## Behavioural rules
- Take briefs from domain agents and execute them fully (visuals + text).
- Always discover brand identity before creating visuals for new clients.
- Optimize prompts for best AI generation quality.
- For text content, ensure SEO optimization and readability.
- Report completion back to the agent who briefed you.
- Use Hinglish when communicating with team.
- If a brief is vague, create the best possible output matching the brand.
- Cross-reference tools: use content briefs to plan visuals, use visual specs to plan text layout.
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


class ContentAgentState(TypedDict):
    messages: Annotated[list[dict[str, Any]], _append_messages]
    workspace_name: str
    client_name: str
    client_context_brief: str  # Pre-built client context for system prompt
    thinking_phases: Annotated[list[dict[str, Any]], _merge_phases]
    tool_round: int
    final_output: str
    brief_from: str  # Which domain agent sent the brief
    tools_used: list[str]  # Track which tools were called
    error: str | None


# ── Helpers ──────────────────────────────────────────────────────────────────

def _extract_content_phases(content: str) -> list[dict[str, Any]]:
    phases = []
    labels = ["deconstruct", "brand_check", "plan", "execute", "deliver"]
    parts = content.split("```think")
    if len(parts) > 1:
        for i, part in enumerate(parts[1:], start=1):
            idx = part.find("```")
            block = part[:idx].strip() if idx != -1 else part.strip()
            label = labels[i - 1] if i - 1 < len(labels) else f"step_{i}"
            phases.append({"phase": label, "content": block})
    return phases


def _strip_think_blocks(content: str) -> str:
    cleaned = re.sub(r"```think.*?```", "", content, flags=re.DOTALL)
    cleaned = re.sub(r"<think>.*?</think>", "", cleaned, flags=re.DOTALL)
    return cleaned.strip()


def _execute_unified_tool(tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Execute a tool by name — tries visual first, then kaggle, then content."""
    # Try visual tools first
    visual_tool_names = {t["function"]["name"] for t in VISUAL_TOOLS}
    if tool_name in visual_tool_names:
        return execute_visual_tool(tool_name, args)

    # Try kaggle tools
    kaggle_tool_names = {"generate_image_kaggle", "generate_video_kaggle"}
    if tool_name in kaggle_tool_names:
        return execute_kaggle_tool(tool_name, args)

    # Try content tools
    content_tool_names = {t["name"] for t in CONTENT_TOOLS}
    if tool_name in content_tool_names:
        return execute_content_tool(tool_name, args)

    return {"error": f"Unknown tool: {tool_name}"}


# ── Graph Nodes ──────────────────────────────────────────────────────────────

async def content_call_llm(state: ContentAgentState) -> dict[str, Any]:
    """Call the LLM with all content tools. Returns tool calls or final response.

    Tool execution happens inline (same pattern as SEO agent).
    After executing tools, results are added to messages and we loop back.
    """
    system = CONTENT_SYSTEM_PROMPT.format(
        workspace_name=state.get("workspace_name", "Default"),
        client_name=state.get("client_name", "Client"),
    )

    # Inject client context into system prompt
    client_brief = state.get("client_context_brief", "")
    if client_brief:
        system += "\n\n" + client_brief

    messages = [{"role": "system", "content": system}]
    messages.extend(state.get("messages", []))

    client = openai.AsyncOpenAI(
        api_key=settings.WORKSPACE_API_KEY or None,
        base_url=settings.WORKSPACE_API_BASE or None,
    )

    try:
        resp = await client.chat.completions.create(
            model=settings.WORKSPACE_AGENT_MODEL,
            messages=messages,
            tools=ALL_CONTENT_TOOLS,
            tool_choice="auto",
            temperature=0.7,
            max_tokens=4096,
        )
    except Exception as e:
        logger.exception("Content Agent LLM call failed")
        return {"error": f"LLM call failed: {str(e)[:200]}"}

    choice = resp.choices[0]
    content = choice.message.content or ""
    tool_calls = choice.message.tool_calls or []

    new_messages = []
    tools_used = list(state.get("tools_used", []))

    if content:
        phases = _extract_content_phases(content)
        if phases:
            new_messages.append({"role": "assistant", "content": content, "tool_calls": []})
            # If there are also tool calls, execute them below
            if not tool_calls:
                return {
                    "messages": new_messages,
                    "thinking_phases": phases,
                    "final_output": content,
                    "tool_round": state.get("tool_round", 0),
                    "tools_used": tools_used,
                }
        if not phases:
            new_messages.append({"role": "assistant", "content": content})

    if tool_calls:
        new_messages.append({
            "role": "assistant",
            "content": content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in tool_calls
            ],
        })

        # Execute tools inline (SEO agent pattern)
        for tc in tool_calls:
            tool_name = tc.function.name
            try:
                args = json.loads(tc.function.arguments)
            except (json.JSONDecodeError, TypeError):
                args = {}

            logger.info("Content tool call: %s(%s)", tool_name, args)
            result = _execute_unified_tool(tool_name, args)
            result_str = json.dumps(result, default=str)[:8000]

            new_messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result_str,
            })

            if tool_name not in tools_used:
                tools_used.append(tool_name)

        # Increment tool_round to prevent infinite loops
        new_tool_round = state.get("tool_round", 0) + 1

        return {
            "messages": new_messages,
            "tool_round": new_tool_round,
            "tools_used": tools_used,
        }

    # No tool calls — this is the final response
    final = _strip_think_blocks(content)
    if not final:
        final = "Content Agent task complete. Check thinking phases for details."

    return {
        "messages": new_messages,
        "final_output": final,
        "tool_round": state.get("tool_round", 0),
        "tools_used": tools_used,
    }


def content_route(state: ContentAgentState) -> str:
    """Route: if tool_calls in last message, loop back to call_llm. Otherwise finalize."""
    msgs = state.get("messages", [])
    if not msgs:
        return "finalize"

    last = msgs[-1]

    # If last message has tool_calls, LLM wants to call tools -> loop back
    if isinstance(last, dict) and last.get("tool_calls"):
        if state.get("tool_round", 0) >= MAX_TOOL_ROUNDS:
            logger.warning("Content Agent hit max tool rounds (%d)", MAX_TOOL_ROUNDS)
            return "finalize"
        return "call_llm"

    # If last message is a tool result, LLM needs to process it -> loop back
    if isinstance(last, dict) and last.get("role") == "tool":
        if state.get("tool_round", 0) >= MAX_TOOL_ROUNDS:
            return "finalize"
        return "call_llm"

    # Otherwise, finalize
    return "finalize"


def content_finalize(state: ContentAgentState) -> dict[str, Any]:
    """Extract the final output from the conversation."""
    output = state.get("final_output", "")
    if output:
        return {"final_output": _strip_think_blocks(output)}

    for msg in reversed(state.get("messages", [])):
        if isinstance(msg, dict) and msg.get("role") == "assistant" and msg.get("content"):
            return {"final_output": _strip_think_blocks(msg["content"])}

    if state.get("error"):
        return {"final_output": f"Content Agent error: {state['error'][:200]}"}
    return {"final_output": "Content Agent task complete."}


# ── Build Graph ──────────────────────────────────────────────────────────────

def build_content_graph() -> StateGraph:
    workflow = StateGraph(ContentAgentState)
    workflow.add_node("call_llm", content_call_llm)
    workflow.add_node("finalize", content_finalize)
    workflow.set_entry_point("call_llm")
    workflow.add_conditional_edges("call_llm", content_route, {
        "call_llm": "call_llm",  # Tool results -> back to LLM
        "finalize": "finalize",  # No more tools -> finalize
    })
    workflow.add_edge("finalize", END)
    return workflow.compile(checkpointer=MemorySaver())


# ── Agent Class ──────────────────────────────────────────────────────────────

class ContentAgent:
    """Content Agent — Full-spectrum content execution for a specific workspace.

    Interview Q4: Per-workspace isolation.
    Interview Q6: Receives briefs from domain agents, reports to briefing agent.
    Interview Q7: Dual reporting — domain agent + Agency Content Agent.
    Interview Q27: Cross-project learning via Agency Content Agent.
    """

    def __init__(
        self,
        workspace_name: str = "Default",
        client_name: str = "Client",
        client_context: dict[str, Any] | None = None,
        _agency_knowledge: str = "",
    ):
        self.graph = build_content_graph()
        self.workspace_name = workspace_name
        self.client_name = client_name
        self.client_context = client_context or {}
        self._thread_id = f"content_{workspace_name}"
        self._agency_knowledge = _agency_knowledge  # Cross-project learnings from Agency Content Agent

    def _build_client_brief(self) -> str:
        """Build a client context brief for the system prompt.

        This tells the Content Agent everything about the client:
        business type, website, industry, target audience, brand colors, style.
        """
        ctx = self.client_context
        if not ctx:
            return ""

        parts = []

        # Business description
        if ctx.get("description"):
            parts.append(f"Client business: {ctx['description']}")

        # Website URL (for brand auto-discovery)
        if ctx.get("website_url"):
            parts.append(f"Client website: {ctx['website_url']}")

        # Industry
        if ctx.get("industry"):
            parts.append(f"Industry: {ctx['industry']}")

        # Target audience
        if ctx.get("target_audience"):
            parts.append(f"Target audience: {ctx['target_audience']}")

        # Brand colors
        if ctx.get("brand_colors"):
            colors = ", ".join(ctx["brand_colors"][:5])
            parts.append(f"Brand colors: {colors}")

        # Brand style
        if ctx.get("brand_style"):
            parts.append(f"Brand visual style: {ctx['brand_style']}")

        # Social links
        if ctx.get("social_links"):
            platforms = ", ".join(ctx["social_links"].keys())
            parts.append(f"Active social platforms: {platforms}")

        # Competitors
        if ctx.get("competitors"):
            parts.append(f"Competitors: {', '.join(ctx['competitors'][:3])}")

        if parts:
            return "\n## CLIENT CONTEXT\n" + "\n".join(f"- {p}" for p in parts)
        return ""

    async def chat(
        self,
        message: str,
        brief_from: str = "",
        conversation_history: list[dict[str, str]] | None = None,
    ) -> tuple[str, list[dict[str, Any]]]:
        """Chat with Content Agent. Returns (response, thinking_phases).

        Dual Reporting (Interview Q7, Q27):
        1. After task completion, reports back to the domain agent that briefed
        2. Also shares learnings with Agency Content Agent for cross-project benefit
        """
        initial_state = {
            "messages": [{"role": "user", "content": message}],
            "workspace_name": self.workspace_name,
            "client_name": self.client_name,
            "client_context_brief": self._build_client_brief(),
            "thinking_phases": [],
            "tool_round": 0,
            "final_output": "",
            "brief_from": brief_from,
            "tools_used": [],
            "error": None,
        }

        # Inject agency cross-project knowledge if available
        if self._agency_knowledge:
            initial_state["messages"].insert(0, {
                "role": "user",
                "content": self._agency_knowledge,
            })

        try:
            result = await self.graph.ainvoke(
                initial_state,
                config={"configurable": {"thread_id": self._thread_id}},
            )
        except Exception:
            logger.exception("Content Agent execution failed")
            return "Content Agent temporarily unavailable.", []

        final_output = result.get("final_output", "")
        thinking_phases = result.get("thinking_phases", [])
        tools_used = result.get("tools_used", [])

        if not final_output:
            if result.get("error"):
                final_output = f"Content Agent error: {result['error'][:200]}"
            else:
                final_output = "Content Agent task complete."

        # ── DUAL REPORTING ────────────────────────────────────────────────
        # 1. Report back to domain agent (operational)
        # 2. Report to Agency Content Agent (cross-project learning)
        self._report_dual(
            brief_from=brief_from,
            final_output=final_output,
            thinking_phases=thinking_phases,
            messages=result.get("messages", []),
            tools_used=tools_used,
        )

        return final_output, thinking_phases

    def _report_dual(
        self,
        brief_from: str,
        final_output: str,
        thinking_phases: list[dict[str, Any]],
        messages: list[dict[str, Any]],
        tools_used: list[str] | None = None,
    ) -> None:
        """Dual reporting after task completion.

        1. Respond to domain agent via agent_bus (operational report)
        2. Send learning report to Agency Content Agent (cross-project)
        """
        tools_used = tools_used or []

        # ── Report 1: Back to domain agent (operational) ──────────────
        if brief_from:
            try:
                send_message(
                    from_agent="content",
                    to_agent=brief_from,
                    workspace_id=self.workspace_name,
                    subject=f"Content Agent report: task complete ({len(tools_used)} tools used)",
                    content=final_output[:2000],
                    message_type="response",
                    metadata={
                        "client": self.client_name,
                        "thinking_phases_count": len(thinking_phases),
                        "tools_used": tools_used,
                    },
                )
                logger.info(
                    "Content Agent reported to domain agent '%s' in workspace '%s'",
                    brief_from, self.workspace_name,
                )
            except Exception as e:
                logger.warning("Failed to report to domain agent '%s': %s", brief_from, e)

        # ── Report 2: Agency Content Agent (cross-project learning) ────
        try:
            agency_agent = get_agency_content_agent()

            # Extract learnings from thinking phases
            learnings = []
            for phase in thinking_phases:
                phase_content = phase.get("content", "")
                if any(kw in phase_content.lower() for kw in ["worked well", "tip", "note", "brand", "effective"]):
                    learnings.append(phase_content[:200])

            # Extract prompts from messages
            prompts_used = []
            for msg in messages:
                if isinstance(msg, dict) and msg.get("role") == "assistant":
                    for tc in msg.get("tool_calls", []):
                        if isinstance(tc, dict):
                            func = tc.get("function", {})
                            args_str = func.get("arguments", "{}")
                            try:
                                args = json.loads(args_str) if isinstance(args_str, str) else args_str
                                if "prompt" in args:
                                    prompts_used.append(args["prompt"][:200])
                            except (json.JSONDecodeError, TypeError):
                                pass

            # Build report
            report = ContentReport(
                report_id=f"rpt_{self.workspace_name}_{len(agency_agent.reports)+1}",
                workspace_name=self.workspace_name,
                client_name=self.client_name,
                brief_from=brief_from,
                brief_summary=final_output[:200],
                deliverables=[f"task_{len(agency_agent.reports)+1}"],
                tools_used=tools_used,
                prompts_used=prompts_used,
                brand_discovered={},
                platform="general",
                visual_type="mixed",
                gpu_minutes=0.0,
                success=True,
                learnings=learnings,
            )

            agency_agent.receive_report(report)
            logger.info(
                "Content Agent reported to Agency Content Agent: %d tools, %d prompts, %d learnings",
                len(tools_used), len(prompts_used), len(learnings),
            )

            # Also share via agent_bus knowledge system
            share_knowledge(
                workspace_id=self.workspace_name,
                key=f"content_tools_used_{brief_from}",
                value=tools_used,
                source_agent="content",
                category="content_tools",
            )

        except Exception as e:
            logger.warning("Failed to report to Agency Content Agent: %s", e)
