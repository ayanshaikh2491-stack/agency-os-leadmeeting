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
from admin.tools.kaggle_tools import KAGGLE_TOOLS, execute_kaggle_tool
from admin.tools.content_tools import CONTENT_TOOLS, execute_content_tool
from admin.tools.content_queue import ContentBrief, get_queue, enhance_brief, JobStatus
from admin.workspace.agent_bus import send_message, share_knowledge
from admin.agency.content_agent import ContentReport, get_agency_content_agent
from admin.workspace.content_store import get_content_store

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 10


# ── Unified Tool Registry ─────────────────────────────────────────────────────

# Merge visual + kaggle + content tools into one unified list for the LLM
ALL_CONTENT_TOOLS = VISUAL_TOOLS + KAGGLE_TOOLS + CONTENT_TOOLS


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
        workspace_id: str = "",
    ):
        self.graph = build_content_graph()
        self.workspace_name = workspace_name
        self.client_name = client_name
        self.client_context = client_context or {}
        self._thread_id = f"content_{workspace_name}"
        self._agency_knowledge = _agency_knowledge
        self._workspace_id = workspace_id or workspace_name
        self._brand_discovered = False  # Track if brand has been auto-discovered

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

    # ── Brand Auto-Discovery ──────────────────────────────────────────────

    async def auto_discover_brand(self) -> dict[str, Any]:
        """Auto-discover client brand from their website.

        Called on first brief if brand info is not in client_context.
        Updates client_context with discovered brand info.
        """
        website_url = self.client_context.get("website_url", "")
        if not website_url:
            return {"status": "no_website", "message": "No website URL in client context"}

        if self._brand_discovered:
            return {"status": "already_discovered", "message": "Brand already discovered"}

        try:
            result = execute_visual_tool("discover_brand_identity", {
                "website_url": website_url,
            })

            if result and not result.get("error"):
                # Merge discovered brand info into client_context
                if result.get("colors") and not self.client_context.get("brand_colors"):
                    self.client_context["brand_colors"] = result["colors"]
                if result.get("visual_style") and not self.client_context.get("brand_style"):
                    self.client_context["brand_style"] = result["visual_style"]
                if result.get("brand_name"):
                    self.client_context["brand_name"] = result["brand_name"]
                if result.get("social_links"):
                    self.client_context["social_links"] = result["social_links"]

                self._brand_discovered = True
                logger.info(
                    "Auto-discovered brand for '%s': %s, %d colors",
                    self.client_name,
                    result.get("brand_name", "Unknown"),
                    len(result.get("colors", [])),
                )
                return {"status": "discovered", "brand": result}

            return {"status": "failed", "error": result.get("error", "Unknown error")}

        except Exception as e:
            logger.warning("Brand auto-discovery failed: %s", e)
            return {"status": "error", "error": str(e)}

    # ── Visual Job Queue Integration ──────────────────────────────────────

    def submit_visual_job(
        self,
        brief_from: str,
        content_type: str,
        platform: str,
        topic: str,
        style: str = "professional",
        quantity: int = 1,
        priority: str = "normal",
        description: str = "",
        text_overlay: str = "",
        cta: str = "",
    ) -> dict[str, Any]:
        """Submit a visual content job to the GPU queue.

        Called by domain agents (Social, Ads, Website) for visual content.
        The brief gets enhanced with brand intelligence before queuing.
        """
        # Auto-discover brand if not done yet
        if not self._brand_discovered and self.client_context.get("website_url"):
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're in an async context but can't await here
                    # Brand discovery will happen on next chat() call
                    pass
                else:
                    loop.run_until_complete(self.auto_discover_brand())
            except Exception:
                pass

        # Create structured brief
        brief = ContentBrief(
            workspace_id=self._workspace_id,
            from_agent=brief_from,
            content_type=content_type,
            platform=platform,
            style=style,
            quantity=quantity,
            topic=topic,
            description=description,
            text_overlay=text_overlay,
            cta=cta,
            priority=priority,
        )

        # Enhance brief with Content Agent intelligence
        enhanced = enhance_brief(brief, self.client_context)

        # Submit to queue
        queue = get_queue(self._workspace_id)
        job_id = queue.submit(enhanced)

        # Record in workspace memory
        try:
            store = get_content_store()
            store.record_brief_received(self._workspace_id, {
                "job_id": job_id,
                "from_agent": brief_from,
                "content_type": content_type,
                "platform": platform,
                "topic": topic,
            })
        except Exception as e:
            logger.warning("Failed to record brief in content store: %s", e)

        # Report submission to domain agent
        if brief_from:
            try:
                send_message(
                    from_agent="content",
                    to_agent=brief_from,
                    workspace_id=self.workspace_name,
                    subject=f"Content job queued: {job_id} ({content_type} for {platform})",
                    content=(
                        f"Job {job_id} has been queued for {content_type} on {platform}.\n"
                        f"Enhanced prompt: {enhanced.enhanced_prompt[:200]}\n"
                        f"Dimensions: {enhanced.width}x{enhanced.height}\n"
                        f"Priority: {priority}"
                    ),
                    message_type="status",
                    metadata={"job_id": job_id, "content_type": content_type},
                )
            except Exception as e:
                logger.warning("Failed to notify domain agent: %s", e)

        logger.info(
            "Visual job submitted: %s (%s %s %dx%d) from %s",
            job_id, content_type, platform, enhanced.width, enhanced.height, brief_from,
        )

        return {
            "job_id": job_id,
            "status": "queued",
            "content_type": content_type,
            "platform": platform,
            "dimensions": f"{enhanced.width}x{enhanced.height}",
            "enhanced_prompt": enhanced.enhanced_prompt[:300],
            "priority": priority,
        }

    async def process_next_job(self) -> dict[str, Any] | None:
        """Process the next job in the queue.

        Called by the scheduler or manually to process queued visual content jobs.
        Returns job result or None if queue is empty.
        """
        queue = get_queue(self._workspace_id)
        job = queue.get_next()

        if not job:
            return None

        logger.info("Processing job: %s (%s)", job.job_id, job.content_type)

        try:
            # Route to appropriate tool based on content type
            if job.content_type in ("video",):
                result = execute_kaggle_tool("generate_video_kaggle", {
                    "prompt": job.enhanced_prompt,
                    "frames": job.frames,
                })
            else:
                result = execute_kaggle_tool("generate_image_kaggle", {
                    "prompt": job.enhanced_prompt,
                    "width": job.width,
                    "height": job.height,
                    "steps": job.steps,
                })

            if result.get("status") in ("submitted", "success") or result.get("output_path"):
                # Kaggle returns "submitted" first — we need to poll for completion
                output_files = []
                kernel_slug = result.get("kernel_slug", "")
                if kernel_slug:
                    # Poll Kaggle until complete
                    import time as _time
                    slug = kernel_slug
                    poll_start = _time.time()
                    while _time.time() - poll_start < 600:  # 10 min timeout
                        status_result = execute_kaggle_tool("check_notebook_status", {"kernel_slug": slug})
                        status_out = status_result.get("output", "").lower()
                        if "complete" in status_out:
                            dl_result = execute_kaggle_tool("download_notebook_output", {"kernel_slug": slug})
                            if dl_result.get("status") == "downloaded":
                                output_files = dl_result.get("files", [])
                                out_dir = dl_result.get("output_dir", "")
                                if out_dir:
                                    for f in os.listdir(out_dir):
                                        fp = os.path.join(out_dir, f)
                                        if f.endswith(".png") or f.endswith(".jpg") or f.endswith(".mp4"):
                                            output_files.append(fp)
                            break
                        elif "error" in status_out or "fail" in status_out:
                            break
                        _time.sleep(15)
                else:
                    output_files = [result.get("output_path", result.get("url", ""))]
                queue.complete(job.job_id, output_files)

                # Record success in workspace memory
                try:
                    store = get_content_store()
                    store.record_success(
                        workspace_id=self._workspace_id,
                        job_id=job.job_id,
                        brief_summary=job.topic or job.description,
                        deliverables=output_files,
                        prompts_used=[job.enhanced_prompt[:200]],
                        platform=job.platform,
                        visual_type=job.content_type,
                        gpu_minutes=0.0,  # TODO: track actual GPU time
                    )
                except Exception as e:
                    logger.warning("Failed to record success: %s", e)

                # Notify domain agent
                if job.from_agent:
                    try:
                        send_message(
                            from_agent="content",
                            to_agent=job.from_agent,
                            workspace_id=self.workspace_name,
                            subject=f"Content job completed: {job.job_id}",
                            content=f"Job {job.job_id} completed. Output: {output_files}",
                            message_type="response",
                            metadata={"job_id": job.job_id, "output_files": output_files},
                        )
                    except Exception:
                        pass

                return {
                    "job_id": job.job_id,
                    "status": "completed",
                    "output_files": output_files,
                }
            else:
                error = result.get("error", "Generation failed")
                will_retry = queue.fail(job.job_id, error)

                # Record failure
                try:
                    store = get_content_store()
                    store.record_failure(
                        workspace_id=self._workspace_id,
                        job_id=job.job_id,
                        brief_summary=job.topic or job.description,
                        error=error,
                        platform=job.platform,
                        visual_type=job.content_type,
                        what_failed=f"{job.content_type} generation failed",
                        avoid_next_time=f"Check GPU availability for {job.content_type}",
                    )
                except Exception:
                    pass

                return {
                    "job_id": job.job_id,
                    "status": "retrying" if will_retry else "failed",
                    "error": error,
                    "retry_count": job.retry_count,
                }

        except Exception as e:
            queue.fail(job.job_id, str(e))
            logger.exception("Job processing failed: %s", job.job_id)
            return {"job_id": job.job_id, "status": "error", "error": str(e)}

    def get_job_status(self, job_id: str) -> dict[str, Any] | None:
        """Get status of a specific job."""
        queue = get_queue(self._workspace_id)
        return queue.get_status(job_id)

    def get_queue_status(self) -> dict[str, Any]:
        """Get overall queue status for this workspace."""
        queue = get_queue(self._workspace_id)
        return queue.get_queue_status()

    def list_recent_jobs(self, limit: int = 10) -> list[dict[str, Any]]:
        """List recent jobs in this workspace."""
        queue = get_queue(self._workspace_id)
        return queue.list_recent(limit)

    # ── Content Approval Workflow ─────────────────────────────────────────

    def request_approval(
        self,
        content_type: str,
        output_summary: str,
        brief_from: str = "",
        output_files: list[str] | None = None,
    ) -> dict[str, Any]:
        """Request CEO approval for content before publishing.

        Stores the content in pending reviews for CEO to approve/reject.
        """
        try:
            from admin.workspace.manager import store_agent_output
            record = store_agent_output(
                workspace_id=self._workspace_id,
                agent_type="content",
                task=f"{content_type}: {output_summary[:100]}",
                output=output_summary,
            )
            logger.info(
                "Content approval requested: %s (record: %s)",
                content_type, record.get("id"),
            )
            return {
                "status": "pending_approval",
                "approval_id": record.get("id"),
                "content_type": content_type,
            }
        except Exception as e:
            logger.warning("Failed to request approval: %s", e)
            return {"status": "error", "error": str(e)}

    def get_memory_summary(self) -> str:
        """Get workspace content agent memory summary."""
        try:
            store = get_content_store()
            return store.get_memory_summary(self._workspace_id)
        except Exception:
            return ""

    def get_stats(self) -> dict[str, Any]:
        """Get workspace content agent stats."""
        try:
            store = get_content_store()
            stats = store.get_stats(self._workspace_id)
            queue_status = self.get_queue_status()
            return {**stats, "queue": queue_status}
        except Exception:
            return {"queue": self.get_queue_status()}

    # ── Process Pending Briefs from Agent Bus ─────────────────────────────

    async def process_pending_briefs(self) -> list[dict[str, Any]]:
        """Poll agent_bus for unread briefs and process them.

        This is the glue between domain agents (who send briefs via bus)
        and Content Agent execution. Call periodically or on-demand.
        
        Returns list of processing results.
        """
        from admin.workspace.agent_bus import get_messages, mark_read, mark_responded
        import asyncio

        # Get unread briefs addressed to content agent
        briefs = get_messages(
            workspace_id=self._workspace_id,
            to_agent="content",
            unread_only=True,
            message_type="brief",
        )
        
        if not briefs:
            return []

        results = []
        for brief in briefs:
            meta = brief.metadata or {}
            content_type = meta.get("content_type", "mixed")
            brief_from = brief.from_agent
            topic = brief.subject or ""
            platform = meta.get("platform", "website")
            style = meta.get("style", "professional")
            description = brief.content or ""

            logger.info(
                "Processing brief from %s: %s (%s)", 
                brief_from, content_type, topic[:60]
            )

            try:
                # Auto-discover brand if needed
                if not self._brand_discovered:
                    await self.auto_discover_brand()

                # Route: visual jobs → submit_visual_job, text/mixed → chat()
                if content_type in ("image", "video", "graphic", "ad", "hero"):
                    job_result = self.submit_visual_job(
                        brief_from=brief_from,
                        content_type=content_type,
                        platform=platform,
                        topic=brief.subject or "",
                        style=style,
                        description=description,
                    )
                    
                    # Also process the next job from queue
                    await self.process_next_job()
                    
                    mark_read(brief.id, self._workspace_id)
                    mark_responded(brief.id, self._workspace_id)
                    
                    results.append({"brief_id": brief.id, "status": "queued", **job_result})
                else:
                    # Text/mixed content → LLM-based processing
                    response, phases = await self.chat(
                        message=(
                            f"You received a brief from {brief_from}.\n"
                            f"Content type: {content_type}\n"
                            f"Platform: {platform}\n"
                            f"Style: {style}\n"
                            f"Description: {description}\n"
                            f"---\n{brief.content}"
                        ),
                        brief_from=brief_from,
                    )
                    
                    mark_read(brief.id, self._workspace_id)
                    mark_responded(brief.id, self._workspace_id)
                    
                    results.append({
                        "brief_id": brief.id,
                        "status": "processed",
                        "response": response[:500],
                    })
            except Exception as e:
                logger.exception("Failed to process brief %s: %s", brief.id, e)
                results.append({"brief_id": brief.id, "status": "error", "error": str(e)})

        return results
