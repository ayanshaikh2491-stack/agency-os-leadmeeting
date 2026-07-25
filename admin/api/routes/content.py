"""Content Agent API Routes — Visual Content Only.

Simple endpoints for:
  - Chat with content agent
  - Generate image/video directly
  - Check job status
  - Get platform specs
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/content", tags=["content-agent"])


# ── Request Models ───────────────────────────────────────────────────────────


class ChatRequest(BaseModel):
    message: str
    workspace_id: str | None = None
    workspace_name: str = "Default"
    client_name: str = "Client"
    brief_from: str = ""  # Which domain agent sent the brief


class GenerateImageRequest(BaseModel):
    prompt: str
    platform: str = "instagram"
    width: int = 0  # 0 = auto from platform
    height: int = 0
    steps: int = 20
    workspace_name: str = "Default"
    client_name: str = "Client"


class GenerateVideoRequest(BaseModel):
    prompt: str
    platform: str = "instagram"
    frames: int = 49  # 49=~6s, 81=~10s
    workspace_name: str = "Default"
    client_name: str = "Client"


class GenerateAdRequest(BaseModel):
    product: str
    platform: str = "facebook"
    style: str = "professional"


class GenerateSocialRequest(BaseModel):
    topic: str
    platform: str = "instagram"


class GenerateHeroRequest(BaseModel):
    topic: str
    style: str = "modern"


class BriefContentAgentRequest(BaseModel):
    """Domain agent briefs Content Agent directly."""
    from_agent: str  # seo, ads, social, website
    workspace_id: str
    task: str
    context: str = ""
    priority: str = "normal"


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.get("/tools")
async def list_tools():
    """Content Agent ke available tools."""
    from admin.tools.kaggle_gpu import PLATFORM_SIZES
    return {
        "tools": [
            "generate_image — FLUX on Kaggle GPU (image)",
            "generate_video — CogVideoX on Kaggle GPU (video)",
            "generate_ad_image — Ad creative image",
            "generate_social_image — Social media image",
            "generate_hero_image — Hero/banner image",
            "get_platform_specs — Image sizes for platforms",
        ],
        "platforms": list(PLATFORM_SIZES.keys()),
    }


@router.get("/status")
async def get_status():
    """Content Agent status."""
    from admin.tools.kaggle_gpu import _check_kaggle
    kaggle_ok = _check_kaggle()
    return {
        "agent": "content",
        "type": "visual_only",
        "gpu_backend": "kaggle",
        "kaggle_cli": kaggle_ok,
        "models": {
            "image": "FLUX.1-dev / SDXL",
            "video": "CogVideoX-2b",
        },
    }


# ── Chat (LangGraph) ────────────────────────────────────────────────────────


@router.post("/chat")
async def chat(req: ChatRequest):
    """Content Agent se chat karo — visual brief bhejo."""
    from admin.workspace.agents.content import run_content_agent

    result = run_content_agent(
        message=req.message,
        workspace_name=req.workspace_name,
        client_name=req.client_name,
        brief_from=req.brief_from,
    )

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))

    return result


# ── Direct Visual Generation ─────────────────────────────────────────────────


@router.post("/generate-image")
async def generate_image_endpoint(req: GenerateImageRequest):
    """Image generate karo — FLUX on Kaggle GPU (on-demand, free)."""
    from admin.tools.kaggle_gpu import generate_image

    result = generate_image(
        prompt=req.prompt,
        platform=req.platform,
        width=req.width,
        height=req.height,
        steps=req.steps,
    )
    return result


@router.post("/generate-video")
async def generate_video_endpoint(req: GenerateVideoRequest):
    """Video generate karo — CogVideoX on Kaggle GPU."""
    from admin.tools.kaggle_gpu import generate_video

    result = generate_video(
        prompt=req.prompt,
        platform=req.platform,
        frames=req.frames,
    )
    return result


@router.post("/generate-ad")
async def generate_ad_endpoint(req: GenerateAdRequest):
    """Ad creative image generate karo."""
    from admin.tools.kaggle_gpu import generate_ad_image

    return generate_ad_image(
        product=req.product,
        platform=req.platform,
        style=req.style,
    )


@router.post("/generate-social")
async def generate_social_endpoint(req: GenerateSocialRequest):
    """Social media image generate karo."""
    from admin.tools.kaggle_gpu import generate_social_image

    return generate_social_image(
        topic=req.topic,
        platform=req.platform,
    )


@router.post("/generate-hero")
async def generate_hero_endpoint(req: GenerateHeroRequest):
    """Hero/banner image generate karo."""
    from admin.tools.kaggle_gpu import generate_hero_image

    return generate_hero_image(
        topic=req.topic,
        style=req.style,
    )


# ── GPU Job Status ───────────────────────────────────────────────────────────


@router.get("/gpu/status/{kernel_slug:path}")
async def gpu_status(kernel_slug: str):
    """Kaggle notebook ka status check karo."""
    from admin.tools.kaggle_gpu import check_status

    status = check_status(kernel_slug)
    return {"kernel_slug": kernel_slug, "status": status}


@router.get("/gpu/platform-specs/{platform}")
async def platform_specs(platform: str):
    """Platform ke image/video size specs."""
    from admin.tools.kaggle_gpu import get_platform_size, PLATFORM_SIZES

    w, h = get_platform_size(platform)
    return {
        "platform": platform,
        "width": w,
        "height": h,
        "all_platforms": {k: {"width": v[0], "height": v[1]} for k, v in PLATFORM_SIZES.items()},
    }


# ── Domain Agent Briefing ────────────────────────────────────────────────────


@router.post("/brief")
async def brief_content_agent(req: BriefContentAgentRequest):
    """Domain agent Content Agent ko brief kare — visual content ke liye."""
    from admin.workspace.agents.content import run_content_agent

    # Build the brief message
    brief_msg = req.task
    if req.context:
        brief_msg += f"\n\nContext: {req.context}"
    brief_msg += f"\n\nPriority: {req.priority}"

    result = run_content_agent(
        message=brief_msg,
        workspace_name=req.workspace_id,
        brief_from=req.from_agent,
    )

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Brief failed"))

    return result
