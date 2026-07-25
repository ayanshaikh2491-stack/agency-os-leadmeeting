"""Content Agent — Visual Content Executor.

VISUAL ONLY. No text, no captions, no copy.

Domain agent sochta hai (text, strategy).
Content Agent banata hai (image, video).

Flow:
  1. Domain agent brief bhejta hai (via agent_bus or direct)
  2. Content Agent parse karta hai: kya chahiye?
  3. Kaggle GPU pe generate karta hai (on-demand)
  4. Output wapas domain agent ko

Simple LangGraph:
  call_llm -> route -> (tool | finalize -> END)
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
    generate_ad_image,
    generate_social_image,
    generate_hero_image,
    get_platform_size,
    check_status,
)

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 6


# ═══════════════════════════════════════════════════════════════════════════════
# STATE
# ═══════════════════════════════════════════════════════════════════════════════

class ContentState(TypedDict):
    messages: Annotated[list[dict[str, Any]], "Conversation messages"]
    workspace_name: str
    client_name: str
    tool_results: Annotated[list[dict[str, Any]], "Results from tool calls"]
    current_tool_calls: Annotated[list[dict[str, Any]], "Pending tool calls"]
    rounds: int


# ═══════════════════════════════════════════════════════════════════════════════
# TOOLS (for LLM function calling)
# ═══════════════════════════════════════════════════════════════════════════════

CONTENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "generate_image",
            "description": "Generate AI image using FLUX on Kaggle GPU. Free 30hrs/week.",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Detailed image description prompt"},
                    "platform": {"type": "string", "description": "Target platform (instagram, facebook, linkedin, twitter, youtube, blog_hero, og_image)", "default": "instagram"},
                    "width": {"type": "integer", "description": "Width in pixels (0 = auto from platform)", "default": 0},
                    "height": {"type": "integer", "description": "Height in pixels (0 = auto from platform)", "default": 0},
                    "steps": {"type": "integer", "description": "FLUX inference steps (20=default, 30=better, 50=best)", "default": 20},
                },
                "required": ["prompt"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_video",
            "description": "Generate AI video using CogVideoX on Kaggle GPU. 5-10 min on T4.",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Detailed video description prompt"},
                    "platform": {"type": "string", "description": "Target platform", "default": "instagram"},
                    "frames": {"type": "integer", "description": "Number of frames (49=~6s, 81=~10s)", "default": 49},
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
                    "platform": {"type": "string", "description": "Platform (facebook, instagram, linkedin, google)", "default": "facebook"},
                    "style": {"type": "string", "description": "Style (professional, bold, minimal, creative)", "default": "professional"},
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
                    "platform": {"type": "string", "description": "Platform (instagram, facebook, twitter, linkedin)", "default": "instagram"},
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
                    "style": {"type": "string", "description": "Style (modern, minimal, bold)", "default": "modern"},
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
                    "platform": {"type": "string", "description": "Platform name"},
                },
                "required": ["platform"],
            },
        },
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT
# ═══════════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """You are the Content Agent for workspace '{workspace_name}' (client: {client_name}).

YOU ARE A VISUAL CONTENT EXECUTOR. You create images and videos ONLY.

## Rules
- You do NOT write text, captions, copy, or blog posts. Domain agents handle text themselves.
- You receive visual briefs from domain agents (SEO, Ads, Social, Website).
- You generate visuals using Kaggle GPU (FLUX for images, CogVideoX for videos).
- GPU is on-demand — you only generate when asked. No background work.

## What You Do
1. **Parse the brief** — What type of visual? What platform? What style?
2. **Build the prompt** — Create a detailed AI image/video prompt from the brief
3. **Generate** — Call the appropriate tool (image or video)
4. **Report** — Tell the domain agent the output is ready

## Platform Sizes (auto-detected)
- Instagram: 1080x1080 (square) or 1080x1350 (portrait)
- Facebook: 1200x630 (post) or 1080x1080 (ad)
- LinkedIn: 1200x627
- Twitter/X: 1200x675
- YouTube thumbnail: 1280x720
- Blog hero: 1200x600

## How to Build Prompts
- Be specific and detailed
- Include: subject, style, colors, mood, composition, lighting
- Example: "A modern fitness Instagram post image, muscular person doing deadlift, bold vibrant colors, motivational atmosphere, gym setting, dramatic lighting, professional photography style, 4k quality"

## Response Format
- Keep responses short and direct
- Always mention: what was generated, where the file is, which platform it's sized for
"""


# ═══════════════════════════════════════════════════════════════════════════════
# TOOL EXECUTION
# ═══════════════════════════════════════════════════════════════════════════════

def _execute_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Tool call execute karo based on name."""
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
            return generate_ad_image(
                product=args["product"],
                platform=args.get("platform", "facebook"),
                style=args.get("style", "professional"),
            )
        elif name == "generate_social_image":
            return generate_social_image(
                topic=args["topic"],
                platform=args.get("platform", "instagram"),
            )
        elif name == "generate_hero_image":
            return generate_hero_image(
                topic=args["topic"],
                style=args.get("style", "modern"),
            )
        elif name == "get_platform_specs":
            w, h = get_platform_size(args["platform"])
            return {"platform": args["platform"], "width": w, "height": h}
        else:
            return {"error": f"Unknown tool: {name}"}
    except Exception as e:
        logger.exception("Tool execution failed: %s", name)
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════════
# LANGGRAPH NODES
# ═══════════════════════════════════════════════════════════════════════════════

def _get_llm_client() -> openai.OpenAI:
    """LLM client banao from settings."""
    api_key = settings.WORKSPACE_API_KEY or settings.AGENCY_CEO_API_KEY or "dummy"
    base_url = settings.WORKSPACE_API_BASE or settings.AGENCY_CEO_API_BASE or None
    return openai.OpenAI(api_key=api_key, base_url=base_url) if base_url else openai.OpenAI(api_key=api_key)


def call_llm(state: ContentState) -> dict[str, Any]:
    """LLM ko message bhejo, tool calls expect karo."""
    messages = list(state["messages"])
    workspace_name = state.get("workspace_name", "Default")
    client_name = state.get("client_name", "Client")

    # Inject system prompt if not present
    if not messages or messages[0].get("role") != "system":
        system_msg = {
            "role": "system",
            "content": SYSTEM_PROMPT.format(
                workspace_name=workspace_name,
                client_name=client_name,
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
        messages.append({"role": "assistant", "content": f"LLM error: {e}"})
        return {"messages": messages}

    choice = response.choices[0]
    assistant_msg = choice.message

    # Add assistant message to history
    msg_dict: dict[str, Any] = {"role": "assistant", "content": assistant_msg.content or ""}
    if assistant_msg.tool_calls:
        msg_dict["tool_calls"] = [
            {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
            for tc in assistant_msg.tool_calls
        ]
    messages.append(msg_dict)

    # Execute tool calls
    tool_results = list(state.get("tool_results", []))
    if assistant_msg.tool_calls:
        for tc in assistant_msg.tool_calls:
            fn_name = tc.function.name
            try:
                fn_args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                fn_args = {}

            logger.info("Tool call: %s(%s)", fn_name, json.dumps(fn_args)[:200])
            result = _execute_tool(fn_name, fn_args)
            tool_results.append({"tool": fn_name, "args": fn_args, "result": result})

            # Add tool result to messages
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
    """Route based on whether LLM made tool calls or wants to finalize."""
    last_msg = state["messages"][-1] if state["messages"] else {}
    has_tool_calls = bool(last_msg.get("tool_calls"))
    rounds = state.get("rounds", 0)

    if has_tool_calls and rounds < MAX_TOOL_ROUNDS:
        return "call_llm"  # Loop back for more tool calls
    return "finalize"


def finalize(state: ContentState) -> dict[str, Any]:
    """Final response — summarize what was generated."""
    messages = list(state["messages"])
    tool_results = state.get("tool_results", [])

    if tool_results:
        summary_parts = []
        for tr in tool_results:
            r = tr.get("result", {})
            if r.get("status") == "success":
                summary_parts.append(f"- {tr['tool']}: {r.get('file', 'generated')} ({r.get('size', '')})")
            elif r.get("status") == "submitted":
                summary_parts.append(f"- {tr['tool']}: submitted to GPU ({r.get('kaggle_url', '')})")
            else:
                summary_parts.append(f"- {tr['tool']}: {r.get('error', r.get('status', 'unknown'))}")

        summary = "Visual content generated:\n" + "\n".join(summary_parts)
        messages.append({"role": "assistant", "content": summary})

    return {"messages": messages}


# ═══════════════════════════════════════════════════════════════════════════════
# LANGGRAPH BUILD
# ═══════════════════════════════════════════════════════════════════════════════

def build_content_graph() -> StateGraph:
    """Content Agent ka LangGraph."""
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


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════

_graph = None


def get_content_graph() -> StateGraph:
    """Singleton graph instance."""
    global _graph
    if _graph is None:
        _graph = build_content_graph()
    return _graph


def run_content_agent(
    message: str,
    workspace_name: str = "Default",
    client_name: str = "Client",
    brief_from: str = "",
    thread_id: str | None = None,
) -> dict[str, Any]:
    """Content Agent ko message bhejo. Returns final response.

    Args:
        message: Visual brief from domain agent
        workspace_name: Workspace name
        client_name: Client name
        brief_from: Which domain agent sent the brief
        thread_id: LangGraph thread ID for conversation continuity

    Returns:
        { "response": "...", "tool_results": [...], "success": bool }
    """
    graph = get_content_graph()

    # Build initial messages
    user_msg = message
    if brief_from:
        user_msg = f"[Brief from {brief_from}] {message}"

    initial_state: dict[str, Any] = {
        "messages": [{"role": "user", "content": user_msg}],
        "workspace_name": workspace_name,
        "client_name": client_name,
        "tool_results": [],
        "current_tool_calls": [],
        "rounds": 0,
    }

    config = {"configurable": {"thread_id": thread_id or f"content_{workspace_name}"}}

    try:
        result = graph.invoke(initial_state, config)
        final_messages = result.get("messages", [])
        last_msg = final_messages[-1] if final_messages else {}

        return {
            "success": True,
            "response": last_msg.get("content", ""),
            "tool_results": result.get("tool_results", []),
            "workspace_name": workspace_name,
            "client_name": client_name,
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


# ═══════════════════════════════════════════════════════════════════════════════
# CONTENT AGENT CLASS (backward compat + simple interface)
# ═══════════════════════════════════════════════════════════════════════════════

class ContentAgent:
    """Visual content executor — creates images and videos via Kaggle GPU.

    Usage:
        agent = ContentAgent(workspace_name="FitnessBrand", client_name="FitPro")
        result = agent.run("Instagram fitness post ki image banao, bold style")
        print(result["response"])
        print(result["tool_results"])
    """

    def __init__(self, workspace_name: str = "Default", client_name: str = "Client"):
        self.workspace_name = workspace_name
        self.client_name = client_name
        self._graph = get_content_graph()

    def run(self, message: str, brief_from: str = "", thread_id: str | None = None) -> dict[str, Any]:
        """Visual brief process karo. Returns {success, response, tool_results}."""
        return run_content_agent(
            message=message,
            workspace_name=self.workspace_name,
            client_name=self.client_name,
            brief_from=brief_from,
            thread_id=thread_id,
        )

    def generate_image(self, prompt: str, platform: str = "instagram", **kwargs) -> dict[str, Any]:
        """Direct image generation — bypass LangGraph."""
        from admin.tools.kaggle_gpu import generate_image as _gen_img
        return _gen_img(prompt=prompt, platform=platform, **kwargs)

    def generate_video(self, prompt: str, platform: str = "instagram", **kwargs) -> dict[str, Any]:
        """Direct video generation — bypass LangGraph."""
        from admin.tools.kaggle_gpu import generate_video as _gen_vid
        return _gen_vid(prompt=prompt, platform=platform, **kwargs)

    def status(self) -> dict[str, Any]:
        """Agent status."""
        from admin.tools.kaggle_gpu import _check_kaggle
        return {
            "agent": "content",
            "workspace": self.workspace_name,
            "client": self.client_name,
            "type": "visual_only",
            "gpu_backend": "kaggle",
            "kaggle_cli": _check_kaggle(),
        }
