"""Content Agent API Routes — Workspace-Aware Visual Content.

Har workspace ka apna Content Agent with brand context.

Endpoints:
  POST /api/content/chat              — Visual brief (with workspace context)
  POST /api/content/init              — Initialize Content Agent for workspace
  POST /api/content/discover-brand    — Discover client brand from website
  POST /api/content/generate-image    — Direct image generation
  POST /api/content/generate-video    — Direct video generation
  POST /api/content/generate-ad       — Ad creative image
  POST /api/content/generate-social   — Social media image
  POST /api/content/generate-hero     — Hero/banner image
  POST /api/content/brief             — Domain agent briefs Content Agent
  GET  /api/content/status/{ws_id}    — Workspace Content Agent status
  GET  /api/content/tools             — Available tools
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/content", tags=["content-agent"])


# ── Request Models ───────────────────────────────────────────────────────────


class InitAgentRequest(BaseModel):
    """Initialize Content Agent for a workspace."""
    workspace_id: str
    workspace_name: str = "Default"
    client_name: str = "Client"
    client_website: str = ""  # Auto-discovers brand if provided


class ChatRequest(BaseModel):
    message: str
    workspace_id: str = ""
    workspace_name: str = "Default"
    client_name: str = "Client"
    client_website: str = ""
    brief_from: str = ""


class DiscoverBrandRequest(BaseModel):
    workspace_id: str
    website_url: str


class GenerateImageRequest(BaseModel):
    prompt: str
    workspace_id: str = ""
    platform: str = "instagram"
    width: int = 0
    height: int = 0
    steps: int = 20


class GenerateVideoRequest(BaseModel):
    prompt: str
    workspace_id: str = ""
    platform: str = "instagram"
    frames: int = 49


class GenerateAdRequest(BaseModel):
    product: str
    workspace_id: str = ""
    platform: str = "facebook"
    style: str = "professional"


class GenerateSocialRequest(BaseModel):
    topic: str
    workspace_id: str = ""
    platform: str = "instagram"


class GenerateHeroRequest(BaseModel):
    topic: str
    workspace_id: str = ""
    style: str = "modern"


class BriefRequest(BaseModel):
    """Domain agent sends detailed visual brief."""
    from_agent: str  # seo, ads, social, website
    workspace_id: str
    workspace_name: str = ""
    client_name: str = ""
    client_website: str = ""
    task: str  # The detailed brief
    context: str = ""
    priority: str = "normal"


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.post("/init")
async def init_agent(req: InitAgentRequest):
    """Content Agent initialize karo workspace ke liye — brand auto-discover hoga."""
    from admin.workspace.agents.content import get_or_create_content_agent

    agent = get_or_create_content_agent(
        workspace_id=req.workspace_id,
        workspace_name=req.workspace_name,
        client_name=req.client_name,
        client_website=req.client_website,
    )

    return {
        "status": "initialized",
        "workspace_id": req.workspace_id,
        "client_name": req.client_name,
        "brand_discovered": bool(agent.brand),
        "brand": agent.brand,
    }


@router.post("/discover-brand")
async def discover_brand(req: DiscoverBrandRequest):
    """Client ka brand discover karo website se."""
    from admin.workspace.agents.content import get_or_create_content_agent

    agent = get_or_create_content_agent(
        workspace_id=req.workspace_id,
        workspace_name=req.workspace_id,
    )
    brand = agent.discover_brand(req.website_url)
    return {"workspace_id": req.workspace_id, "brand": brand}


@router.get("/status/{workspace_id}")
async def get_status(workspace_id: str):
    """Workspace Content Agent ka status."""
    from admin.workspace.agents.content import get_content_agent

    agent = get_content_agent(workspace_id)
    if not agent:
        return {"status": "not_initialized", "workspace_id": workspace_id}

    return agent.status()


@router.get("/tools")
async def list_tools():
    """Available tools."""
    return {
        "tools": [
            "generate_image — FLUX on Kaggle GPU",
            "generate_video — CogVideoX on Kaggle GPU",
            "generate_ad_image — Ad creative",
            "generate_social_image — Social media image",
            "generate_hero_image — Hero/banner",
            "get_platform_specs — Platform sizes",
        ],
        "type": "visual_only",
    }


# ── Chat (LangGraph — brand-aware thinking) ──────────────────────────────────


@router.post("/chat")
async def chat(req: ChatRequest):
    """Content Agent se visual brief chatta hai — brand context + thinking ke saath."""
    from admin.workspace.agents.content import run_content_agent

    result = run_content_agent(
        message=req.message,
        workspace_id=req.workspace_id,
        workspace_name=req.workspace_name,
        client_name=req.client_name,
        client_website=req.client_website,
        brief_from=req.brief_from,
    )

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Unknown"))

    return result


# ── Direct Generation ────────────────────────────────────────────────────────


@router.post("/generate-image")
async def generate_image_endpoint(req: GenerateImageRequest):
    """Image generate karo — direct API."""
    from admin.tools.kaggle_gpu import generate_image

    return generate_image(
        prompt=req.prompt,
        platform=req.platform,
        width=req.width,
        height=req.height,
        steps=req.steps,
    )


@router.post("/generate-video")
async def generate_video_endpoint(req: GenerateVideoRequest):
    """Video generate karo — direct API."""
    from admin.tools.kaggle_gpu import generate_video

    return generate_video(
        prompt=req.prompt,
        platform=req.platform,
        frames=req.frames,
    )


@router.post("/generate-ad")
async def generate_ad_endpoint(req: GenerateAdRequest):
    """Ad creative image."""
    from admin.tools.kaggle_gpu import generate_image

    prompt = f"A professional {req.style} advertisement for {req.product}, high quality marketing material"
    return generate_image(prompt=prompt, platform=req.platform)


@router.post("/generate-social")
async def generate_social_endpoint(req: GenerateSocialRequest):
    """Social media image."""
    from admin.tools.kaggle_gpu import generate_image

    prompt = f"A beautiful, engaging social media post about {req.topic}, modern design, vibrant colors, professional quality"
    return generate_image(prompt=prompt, platform=req.platform)


@router.post("/generate-hero")
async def generate_hero_endpoint(req: GenerateHeroRequest):
    """Hero/banner image."""
    from admin.tools.kaggle_gpu import generate_image

    prompt = f"A stunning hero banner image about {req.topic}, {req.style} design, wide format, professional quality"
    return generate_image(prompt=prompt, platform="blog_hero", width=1920, height=1080)


# ── Domain Agent Briefing ────────────────────────────────────────────────────


@router.post("/brief")
async def brief_content_agent(req: BriefRequest):
    """Domain agent Content Agent ko detailed brief bhejta hai.

    Content Agent:
      1. Brief parse karega
      2. Brand context dekhega
      3. Visual plan banayega
      4. Expert prompt engineering karega
      5. Kaggle GPU pe generate karega
      6. Report karega
    """
    from admin.workspace.agents.content import run_content_agent

    brief_msg = req.task
    if req.context:
        brief_msg += f"\n\nAdditional Context: {req.context}"
    brief_msg += f"\n\nPriority: {req.priority}"

    result = run_content_agent(
        message=brief_msg,
        workspace_id=req.workspace_id,
        workspace_name=req.workspace_name or req.workspace_id,
        client_name=req.client_name,
        client_website=req.client_website,
        brief_from=req.from_agent,
    )

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Brief failed"))

    return result


# ── GPU Status ───────────────────────────────────────────────────────────────


@router.get("/gpu/status/{kernel_slug:path}")
async def gpu_status(kernel_slug: str):
    """Kaggle notebook status."""
    from admin.tools.kaggle_gpu import check_status
    return {"kernel_slug": kernel_slug, "status": check_status(kernel_slug)}
