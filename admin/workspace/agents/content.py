"""Content Agent — Workspace-Aware Visual Content Executor.

HAR workspace ka apna Content Agent hoga jo us client ko jaanta hai:
  - Brand name, logo, colors, visual style
  - Past successes/failures, learnings
  - Industry tips, platform performance

Flow:
  1. Workspace created → Content Agent initialized
     → Brand discover hota hai website se
     → Memory load hoti hai (past work)
     → Brand context ready hai

  2. Domain Agent brief bhejta hai (detailed)
     → "Instagram post chahiye — fitness, bold style, red+black"

  3. Content Agent SOCHTA hai (LangGraph pipeline):
     Step 1: Brief samjhe — kya chahiye, kyun, kis platform pe
     Step 2: Brand context dekhe — client ke colors, style, tone
     Step 3: Visual plan banaye — composition, layout, elements
     Step 4: Expert prompt likhe — FLUX ko clear samajh aaye
     Step 5: Generate kare — Kaggle GPU pe submit
     Step 6: Report kare — domain agent ko wapas

VISUAL ONLY — no text, no captions, no copy.
"""
from __future__ import annotations

import json
import logging
from typing import Annotated, Any, TypedDict

import openai
from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from admin.config import settings
from admin.tools.kaggle_gpu import (
    generate_visual,
    generate_image,
    generate_video,
    get_platform_size,
    PLATFORM_SIZES,
)
from admin.tools.visual_tools import discover_brand_identity
from admin.workspace.content_store import WorkspaceContentStore

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 8


# ═══════════════════════════════════════════════════════════════════════════════
# CONTENT STORE (per-workspace memory)
# ═══════════════════════════════════════════════════════════════════════════════

_content_store = WorkspaceContentStore()


# ═══════════════════════════════════════════════════════════════════════════════
# STATE
# ═══════════════════════════════════════════════════════════════════════════════

class ContentState(TypedDict):
    messages: Annotated[list[dict[str, Any]], "Conversation"]
    workspace_id: str
    workspace_name: str
    client_name: str
    client_website: str
    brand_context: dict[str, Any]  # Brand info (colors, style, logo)
    brief_from: str  # Which domain agent
    tool_results: Annotated[list[dict[str, Any]], "Tool outputs"]
    current_tool_calls: Annotated[list[dict[str, Any]], "Pending calls"]
    rounds: int


# ═══════════════════════════════════════════════════════════════════════════════
# TOOLS (for LLM function calling)
# ═══════════════════════════════════════════════════════════════════════════════

CONTENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "generate_image",
            "description": "Generate AI image using FLUX on Kaggle GPU. Pass the FINAL engineered prompt — detailed, specific, ready for AI generation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "Expert-level image prompt. Must be detailed: subject, action, style, colors, mood, composition, lighting, quality. Example: 'A muscular person doing deadlift in a modern gym, bold red and black color scheme matching brand identity, dramatic side lighting, motivational atmosphere, professional fitness photography, 4k ultra detailed'",
                    },
                    "platform": {"type": "string", "description": "instagram, facebook, linkedin, twitter, youtube, blog_hero, og_image", "default": "instagram"},
                    "width": {"type": "integer", "description": "Width (0=auto from platform)", "default": 0},
                    "height": {"type": "integer", "description": "Height (0=auto from platform)", "default": 0},
                    "steps": {"type": "integer", "description": "20=default, 30=better, 50=best quality", "default": 20},
                },
                "required": ["prompt"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_video",
            "description": "Generate AI video using CogVideoX on Kaggle GPU.",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Detailed video prompt with motion, style, mood"},
                    "platform": {"type": "string", "default": "instagram"},
                    "frames": {"type": "integer", "description": "49=~6s, 81=~10s", "default": 49},
                },
                "required": ["prompt"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_ad_image",
            "description": "Generate ad creative image for specific platform.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product": {"type": "string", "description": "Product/service to advertise"},
                    "platform": {"type": "string", "default": "facebook"},
                    "style": {"type": "string", "description": "professional, bold, minimal, creative", "default": "professional"},
                },
                "required": ["product"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_social_image",
            "description": "Generate social media post image.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Post topic"},
                    "platform": {"type": "string", "default": "instagram"},
                },
                "required": ["topic"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_hero_image",
            "description": "Generate hero/banner image for blog or website.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Hero image topic"},
                    "style": {"type": "string", "default": "modern"},
                },
                "required": ["topic"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_platform_specs",
            "description": "Get image/video size specs for any platform.",
            "parameters": {
                "type": "object",
                "properties": {
                    "platform": {"type": "string"},
                },
                "required": ["platform"],
            },
        },
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT — Content Agent ka dimag
# ═══════════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """You are the Content Agent for workspace '{workspace_name}' (client: {client_name}).

YOU ARE A VISUAL CONTENT EXECUTOR. You create images and videos ONLY.
You do NOT write text, captions, copy, or blog posts.

## Your Client's Brand Identity
{brand_context}

## Your Past Learnings
{workspace_memory}

## Your Job
Domain agents send you DETAILED visual briefs. You must:
1. UNDERSTAND the brief deeply — what type of visual, why, for whom
2. APPLY brand identity — use client's colors, style, tone
3. PLAN the visual — composition, layout, elements, mood
4. ENGINEER the prompt — create expert-level AI generation prompt
5. GENERATE — submit to Kaggle GPU
6. REPORT back with what was created

## How to Think (BEFORE calling any tool)

When a domain agent sends you a brief, think through these steps:

### Step 1: Parse Brief
- What type of visual? (image, video, ad, social post, hero banner)
- What platform? (instagram, facebook, linkedin, etc.)
- What's the topic/subject?
- What mood/style? (bold, minimal, professional, fun)
- Is there text overlay or CTA?
- What's the target audience?

### Step 2: Brand Context
- Client's primary colors: {primary_colors}
- Client's visual style: {visual_style}
- Client's brand name: {brand_name}
- Use these in the visual — don't ignore brand identity!

### Step 3: Visual Plan
Before calling generate_image, describe:
- COMPOSITION: Where is the subject? What's the focal point?
- LAYOUT: Center, rule of thirds, diagonal, symmetrical?
- ELEMENTS: What objects/people/graphics appear?
- COLORS: How do brand colors apply here?
- LIGHTING: Natural, dramatic, studio, backlit?
- TEXT SPACE: Is there room for text overlay?

### Step 4: Build Expert Prompt
The prompt must be DETAILED and SPECIFIC. Bad prompt: "fitness image"
Good prompt: "A muscular person performing a deadlift in a modern gym, bold red (#E63946) and black color scheme, dramatic side lighting creating strong shadows, motivational atmosphere, professional fitness photography style, 4k ultra detailed, clean composition with space for text overlay on the right side"

## Platform Sizes (auto-detected)
- Instagram: 1080x1080 (square), 1080x1350 (portrait), 1080x1920 (story)
- Facebook: 1200x630 (post), 1080x1080 (ad)
- LinkedIn: 1200x627
- Twitter/X: 1200x675
- YouTube: 1280x720 (thumbnail)
- Blog: 1200x600 (hero)

## Rules
- VISUAL ONLY — never write text content
- Always use brand colors when possible
- Always consider the platform dimensions
- Be specific in prompts — vague prompts = bad images
- Report back with file path when done
"""


# ═══════════════════════════════════════════════════════════════════════════════
# TOOL EXECUTION
# ═══════════════════════════════════════════════════════════════════════════════

def _execute_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Tool call execute karo."""
    try:
        if name == "generate_image":
            return generate_image(
                prompt=args["prompt"],
                platform=args.get("platform", "instagram"),
                width=args.get("width", 0),
                height=args.get("height", 0),
                steps=args.get("steps", 20),
            )
        elif name == "generate_video":
            return generate_video(
                prompt=args["prompt"],
                platform=args.get("platform", "instagram"),
                frames=args.get("frames", 49),
            )
        elif name == "generate_ad_image":
            return generate_image(
                prompt=f"A professional {args.get('style', 'professional')} advertisement for {args['product']}, high quality marketing material",
                platform=args.get("platform", "facebook"),
            )
        elif name == "generate_social_image":
            return generate_image(
                prompt=f"A beautiful, engaging social media post about {args['topic']}, modern design, vibrant colors, professional quality",
                platform=args.get("platform", "instagram"),
            )
        elif name == "generate_hero_image":
            return generate_image(
                prompt=f"A stunning hero banner image about {args['topic']}, {args.get('style', 'modern')} design, wide format, professional quality",
                platform="blog_hero",
                width=1920,
                height=1080,
            )
        elif name == "get_platform_specs":
            w, h = get_platform_size(args["platform"])
            return {"platform": args["platform"], "width": w, "height": h}
        else:
            return {"error": f"Unknown tool: {name}"}
    except Exception as e:
        logger.exception("Tool failed: %s", name)
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER: Format brand context for system prompt
# ═══════════════════════════════════════════════════════════════════════════════

def _format_brand_context(brand: dict[str, Any]) -> str:
    """Brand context ko human-readable format mein convert karo."""
    if not brand:
        return "No brand info available yet. Will discover from website if URL provided."

    parts = []
    if brand.get("brand_name"):
        parts.append(f"- Brand Name: {brand['brand_name']}")
    if brand.get("colors"):
        parts.append(f"- Brand Colors: {', '.join(brand['colors'][:5])}")
    if brand.get("visual_style"):
        parts.append(f"- Visual Style: {brand['visual_style']}")
    if brand.get("logo_url"):
        parts.append(f"- Logo: {brand['logo_url']}")
    if brand.get("social_links"):
        platforms = list(brand["social_links"].keys())
        parts.append(f"- Social Platforms: {', '.join(platforms)}")
    if brand.get("meta_info", {}).get("description"):
        desc = brand["meta_info"]["description"][:200]
        parts.append(f"- Brand Description: {desc}")

    return "\n".join(parts) if parts else "No brand info available."


def _format_workspace_memory(workspace_id: str) -> str:
    """Workspace ki past learnings load karo."""
    mem = _content_store._memories.get(workspace_id)
    if not mem:
        return "No past work yet — this is the first brief for this workspace."

    parts = []
    if mem.brand_learnings:
        parts.append("Brand Learnings:")
        for l in mem.brand_learnings[:5]:
            parts.append(f"  - {l}")
    if mem.mistakes_to_avoid:
        parts.append("Mistakes to Avoid:")
        for m in mem.mistakes_to_avoid[:3]:
            parts.append(f"  - {m}")
    if mem.industry_tips:
        parts.append("Industry Tips:")
        for t in mem.industry_tips[:3]:
            parts.append(f"  - {t}")
    if mem.success_count > 0:
        parts.append(f"Past Successes: {mem.success_count}")
    if mem.failure_count > 0:
        parts.append(f"Past Failures: {mem.failure_count}")

    return "\n".join(parts) if parts else "No past work yet."


def _get_primary_colors(brand: dict[str, Any]) -> str:
    colors = brand.get("colors", [])
    return ", ".join(colors[:5]) if colors else "No brand colors detected"


def _get_visual_style(brand: dict[str, Any]) -> str:
    return brand.get("visual_style", "Not detected yet")


def _get_brand_name(brand: dict[str, Any]) -> str:
    return brand.get("brand_name", "Unknown")


# ═══════════════════════════════════════════════════════════════════════════════
# LANGGRAPH NODES
# ═══════════════════════════════════════════════════════════════════════════════

def _get_llm_client() -> openai.OpenAI:
    api_key = settings.WORKSPACE_API_KEY or settings.AGENCY_CEO_API_KEY or "dummy"
    base_url = settings.WORKSPACE_API_BASE or settings.AGENCY_CEO_API_BASE or None
    return openai.OpenAI(api_key=api_key, base_url=base_url) if base_url else openai.OpenAI(api_key=api_key)


def call_llm(state: ContentState) -> dict[str, Any]:
    """LLM ko message bhejo — brand context + memory ke saath."""
    messages = list(state["messages"])
    brand = state.get("brand_context", {})

    # System prompt with brand context
    system_msg = {
        "role": "system",
        "content": SYSTEM_PROMPT.format(
            workspace_name=state.get("workspace_name", "Default"),
            client_name=state.get("client_name", "Client"),
            brand_context=_format_brand_context(brand),
            workspace_memory=_format_workspace_memory(state.get("workspace_id", "")),
            primary_colors=_get_primary_colors(brand),
            visual_style=_get_visual_style(brand),
            brand_name=_get_brand_name(brand),
        ),
    }
    messages = [system_msg] + messages

    client = _get_llm_client()
    model = settings.WORKSPACE_AGENT_MODEL or "llama-3.3-70b-versatile"

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=CONTENT_TOOLS,
            tool_choice="auto",
            temperature=0.3,
            max_tokens=2000,
        )
    except Exception as e:
        logger.exception("LLM call failed")
        messages.append({"role": "assistant", "content": f"Error: {e}"})
        return {"messages": messages}

    choice = response.choices[0]
    assistant_msg = choice.message

    # Add assistant message
    msg_dict: dict[str, Any] = {"role": "assistant", "content": assistant_msg.content or ""}
    if assistant_msg.tool_calls:
        msg_dict["tool_calls"] = [
            {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
            for tc in assistant_msg.tool_calls
        ]
    messages.append(msg_dict)

    # Execute tools
    tool_results = list(state.get("tool_results", []))
    if assistant_msg.tool_calls:
        for tc in assistant_msg.tool_calls:
            fn_name = tc.function.name
            try:
                fn_args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                fn_args = {}

            logger.info("Tool: %s(%s)", fn_name, json.dumps(fn_args)[:200])
            result = _execute_tool(fn_name, fn_args)
            tool_results.append({"tool": fn_name, "args": fn_args, "result": result})

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result, default=str),
            })

    return {
        "messages": messages,
        "tool_results": tool_results,
        "current_tool_calls": [
            {"name": tc.function.name, "args": tc.function.arguments}
            for tc in (assistant_msg.tool_calls or [])
        ],
        "rounds": state.get("rounds", 0) + 1,
    }


def route_from_llm(state: ContentState) -> str:
    """Route: tool calls → loop, no calls → finalize."""
    last_msg = state["messages"][-1] if state["messages"] else {}
    has_tool_calls = bool(last_msg.get("tool_calls"))
    rounds = state.get("rounds", 0)

    if has_tool_calls and rounds < MAX_TOOL_ROUNDS:
        return "call_llm"
    return "finalize"


def finalize(state: ContentState) -> dict[str, Any]:
    """Final response — summarize what was generated."""
    messages = list(state["messages"])
    tool_results = state.get("tool_results", [])
    workspace_id = state.get("workspace_id", "")

    if tool_results:
        for tr in tool_results:
            r = tr.get("result", {})
            # Record to content store memory
            if r.get("status") == "success":
                _content_store.record_success(
                    workspace_id=workspace_id,
                    job_id=r.get("kernel_slug", ""),
                    brief_summary=tr.get("args", {}).get("prompt", "")[:200],
                    deliverables=[r.get("file", "")],
                    prompts_used=[tr.get("args", {}).get("prompt", "")],
                    platform=tr.get("args", {}).get("platform", "instagram"),
                    visual_type=tr["tool"],
                    gpu_minutes=r.get("elapsed_seconds", 0) / 60,
                )
            elif r.get("status") in ("error", "submit_failed"):
                _content_store.record_failure(
                    workspace_id=workspace_id,
                    job_id=r.get("kernel_slug", ""),
                    brief_summary=tr.get("args", {}).get("prompt", "")[:200],
                    error=r.get("error", "Unknown"),
                )

    return {"messages": messages}


# ═══════════════════════════════════════════════════════════════════════════════
# LANGGRAPH BUILD
# ═══════════════════════════════════════════════════════════════════════════════

def build_content_graph() -> StateGraph:
    graph = StateGraph(ContentState)
    graph.add_node("call_llm", call_llm)
    graph.add_node("finalize", finalize)
    graph.set_entry_point("call_llm")
    graph.add_conditional_edges("call_llm", route_from_llm, {
        "call_llm": "call_llm",
        "finalize": "finalize",
    })
    graph.add_edge("finalize", END)
    return graph.compile(checkpointer=MemorySaver())


_graph = None

def get_content_graph() -> StateGraph:
    global _graph
    if _graph is None:
        _graph = build_content_graph()
    return _graph


# ═══════════════════════════════════════════════════════════════════════════════
# CONTENT AGENT CLASS — workspace-aware
# ═══════════════════════════════════════════════════════════════════════════════

class ContentAgent:
    """Workspace-specific Content Agent — knows its client's brand.

    Usage:
        # Workspace create hote hi Content Agent init hota hai
        agent = ContentAgent(
            workspace_id="ws_fitpro_001",
            workspace_name="FitPro Fitness",
            client_name="FitPro",
            client_website="https://fitpro.com",
        )

        # Brand auto-discover hota hai
        print(agent.brand)  # {colors: ["#E63946", "#1D3557"], style: "bold", ...}

        # Domain agent brief bhejta hai
        result = agent.run(
            message="[Brief from social] Instagram fitness post chahiye...",
            brief_from="social",
        )
    """

    def __init__(
        self,
        workspace_id: str = "",
        workspace_name: str = "Default",
        client_name: str = "Client",
        client_website: str = "",
    ):
        self.workspace_id = workspace_id
        self.workspace_name = workspace_name
        self.client_name = client_name
        self.client_website = client_website
        self.brand: dict[str, Any] = {}
        self._graph = get_content_graph()

        # Load or create memory for this workspace
        _content_store.get_or_create(
            workspace_id=workspace_id,
            workspace_name=workspace_name,
            client_name=client_name,
        )

        # Auto-discover brand if website provided
        if client_website:
            self.discover_brand(client_website)

    def discover_brand(self, website_url: str = "") -> dict[str, Any]:
        """Client ka brand discover karo website se."""
        url = website_url or self.client_website
        if not url:
            return {}

        logger.info("Discovering brand for %s from %s", self.client_name, url)
        self.brand = discover_brand_identity(url)

        # Save brand info to content store
        mem = _content_store._memories.get(self.workspace_id)
        if mem and self.brand.get("brand_name"):
            if self.brand["brand_name"] not in mem.brand_learnings:
                mem.brand_learnings.append(f"Brand: {self.brand['brand_name']}")
            for color in self.brand.get("colors", [])[:3]:
                learning = f"Brand color: {color}"
                if learning not in mem.brand_learnings:
                    mem.brand_learnings.append(learning)
            if self.brand.get("visual_style"):
                tip = f"Visual style: {self.brand['visual_style']}"
                if tip not in mem.industry_tips:
                    mem.industry_tips.append(tip)
            _content_store._save(self.workspace_id)

        return self.brand

    def run(
        self,
        message: str,
        brief_from: str = "",
        thread_id: str | None = None,
    ) -> dict[str, Any]:
        """Domain agent ka brief process karo.

        Content Agent sochega:
          1. Brief samjhega
          2. Brand context dekhega
          3. Visual plan banayega
          4. Expert prompt likhega
          5. Generate karega
          6. Report karega
        """
        graph = self._graph

        user_msg = message
        if brief_from:
            user_msg = f"[Brief from {brief_from}] {message}"

        initial_state: dict[str, Any] = {
            "messages": [{"role": "user", "content": user_msg}],
            "workspace_id": self.workspace_id,
            "workspace_name": self.workspace_name,
            "client_name": self.client_name,
            "client_website": self.client_website,
            "brand_context": self.brand,
            "brief_from": brief_from,
            "tool_results": [],
            "current_tool_calls": [],
            "rounds": 0,
        }

        config = {"configurable": {"thread_id": thread_id or f"content_{self.workspace_id}"}}

        try:
            result = graph.invoke(initial_state, config)
            final_messages = result.get("messages", [])
            last_msg = final_messages[-1] if final_messages else {}

            return {
                "success": True,
                "response": last_msg.get("content", ""),
                "tool_results": result.get("tool_results", []),
                "brand_used": self.brand,
                "workspace_name": self.workspace_name,
                "client_name": self.client_name,
                "brief_from": brief_from,
            }
        except Exception as e:
            logger.exception("Content agent failed")
            return {
                "success": False,
                "error": str(e),
                "response": f"Content Agent error: {e}",
                "tool_results": [],
            }

    def generate_image(self, prompt: str, platform: str = "instagram", **kwargs) -> dict[str, Any]:
        """Direct image generation — bypass LangGraph."""
        return generate_image(prompt=prompt, platform=platform, **kwargs)

    def generate_video(self, prompt: str, platform: str = "instagram", **kwargs) -> dict[str, Any]:
        """Direct video generation — bypass LangGraph."""
        return generate_video(prompt=prompt, platform=platform, **kwargs)

    def status(self) -> dict[str, Any]:
        """Agent status."""
        from admin.tools.kaggle_gpu import _check_kaggle
        mem = _content_store._memories.get(self.workspace_id)
        return {
            "agent": "content",
            "workspace_id": self.workspace_id,
            "workspace_name": self.workspace_name,
            "client_name": self.client_name,
            "client_website": self.client_website,
            "brand_discovered": bool(self.brand),
            "brand_colors": self.brand.get("colors", []),
            "brand_style": self.brand.get("visual_style", ""),
            "kaggle_cli": _check_kaggle(),
            "past_successes": mem.success_count if mem else 0,
            "past_failures": mem.failure_count if mem else 0,
        }


# ═══════════════════════════════════════════════════════════════
# WORKSPACE AGENT REGISTRY
# ═══════════════════════════════════════════════════════════════════════════════

_agents: dict[str, ContentAgent] = {}


def get_or_create_content_agent(
    workspace_id: str,
    workspace_name: str = "",
    client_name: str = "",
    client_website: str = "",
) -> ContentAgent:
    """Get existing Content Agent for workspace, or create new one."""
    if workspace_id in _agents:
        return _agents[workspace_id]

    agent = ContentAgent(
        workspace_id=workspace_id,
        workspace_name=workspace_name or workspace_id,
        client_name=client_name or workspace_name,
        client_website=client_website,
    )
    _agents[workspace_id] = agent
    return agent


def get_content_agent(workspace_id: str) -> ContentAgent | None:
    """Get Content Agent for workspace."""
    return _agents.get(workspace_id)


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════

def run_content_agent(
    message: str,
    workspace_id: str = "",
    workspace_name: str = "",
    client_name: str = "",
    client_website: str = "",
    brief_from: str = "",
    thread_id: str | None = None,
) -> dict[str, Any]:
    """Content Agent ko brief bhejo — auto-creates workspace agent if needed."""
    agent = get_or_create_content_agent(
        workspace_id=workspace_id,
        workspace_name=workspace_name,
        client_name=client_name,
        client_website=client_website,
    )
    return agent.run(
        message=message,
        brief_from=brief_from,
        thread_id=thread_id,
    )
