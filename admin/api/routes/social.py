"""Social Agent API Routes — Organic Social Media strategist endpoints.

Endpoints:
  POST /api/social/chat               — Chat with Social Agent
  POST /api/social/calendar           — Generate content calendar
  POST /api/social/hashtags           — Hashtag research
  POST /api/social/schedule           — Best posting times
  POST /api/social/competitors        — Competitor analysis
  POST /api/social/trends             — Trend research
  POST /api/social/engagement         — Engagement strategy
  POST /api/social/platform           — Platform strategy
  POST /api/social/gaps               — Content gap analysis
  POST /api/social/audience           — Audience analysis
  POST /api/social/growth             — Growth tactics
  POST /api/social/caption            — Generate post caption
  POST /api/social/repurpose          — Repurpose content for platforms
  POST /api/social/dm-outreach        — DM outreach templates
  POST /api/social/influencers        — Influencer research
  POST /api/social/analytics          — Analytics report
  POST /api/social/request-content    — Brief Content Agent
  GET  /api/social/tools              — Available tools
"""
from __future__ import annotations

import logging

from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/social", tags=["social-agent"])


# ── Request Models ───────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    workspace_name: str = "Default"
    client_name: str = "Client"


class CalendarRequest(BaseModel):
    platform: str = "instagram"
    duration: str = "1 week"
    niche: str = ""
    brand_tone: str = "professional"


class HashtagRequest(BaseModel):
    niche: str = ""
    platform: str = "instagram"
    count: int = 30


class ScheduleRequest(BaseModel):
    platform: str = "instagram"
    timezone_offset: int = 5
    audience: str = "general"


class CompetitorRequest(BaseModel):
    competitors: list[str]
    platform: str = "instagram"
    niche: str = ""


class TrendRequest(BaseModel):
    niche: str = ""
    platform: str = "instagram"


class EngagementRequest(BaseModel):
    platform: str = "instagram"
    goals: str = "community building"
    audience_size: str = "small"


class PlatformRequest(BaseModel):
    industry: str = ""
    goals: str = "brand awareness"
    budget: str = "organic_only"


class GapRequest(BaseModel):
    your_content: list[str]
    competitor_content: list[str]
    niche: str = ""


class AudienceRequest(BaseModel):
    industry: str = ""
    platform: str = "instagram"
    location: str = "India"


class GrowthRequest(BaseModel):
    current_followers: int = 0
    platform: str = "instagram"
    niche: str = ""
    budget: str = "organic"


class RequestContentRequest(BaseModel):
    workspace_name: str = "Default"
    content_type: str = "carousel"
    topic: str = ""
    platform: str = "instagram"
    description: str = ""
    style: str = "bold"
    priority: str = "normal"
    quantity: int = 1


class CaptionRequest(BaseModel):
    topic: str = ""
    platform: str = "instagram"
    tone: str = "engaging"
    audience: str = "general"
    include_cta: bool = True


class RepurposeRequest(BaseModel):
    original_content: str = ""
    source_platform: str = "instagram"
    target_platforms: list[str] = ["linkedin", "twitter", "tiktok", "facebook"]
    topic: str = ""


class DMOutreachRequest(BaseModel):
    purpose: str = "collaboration"
    platform: str = "instagram"
    target_audience: str = "micro-influencers"
    tone: str = "friendly"


class InfluencerRequest(BaseModel):
    niche: str = ""
    platform: str = "instagram"
    budget: str = "organic"
    count: int = 10


class AnalyticsRequest(BaseModel):
    platform: str = "instagram"
    metrics: list[str] = ["followers", "engagement", "reach"]
    period: str = "weekly"


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/chat")
async def chat(req: ChatRequest):
    """Chat with Social Agent."""
    from admin.workspace.agents.social import SocialAgent
    agent = SocialAgent(workspace_name=req.workspace_name, client_name=req.client_name)
    output, thread_id = await agent.chat(req.message)
    return {"response": output, "thread_id": thread_id}


@router.post("/calendar")
async def calendar(req: CalendarRequest):
    """Generate content calendar."""
    from admin.tools.social_tools import content_calendar
    return content_calendar(req.platform, req.duration, req.niche, req.brand_tone)


@router.post("/hashtags")
async def hashtags(req: HashtagRequest):
    """Hashtag research."""
    from admin.tools.social_tools import hashtag_research
    return hashtag_research(req.niche, req.platform, req.count)


@router.post("/schedule")
async def schedule(req: ScheduleRequest):
    """Best posting times."""
    from admin.tools.social_tools import posting_schedule
    return posting_schedule(req.platform, req.timezone_offset, req.audience)


@router.post("/competitors")
async def competitors(req: CompetitorRequest):
    """Competitor analysis."""
    from admin.tools.social_tools import competitor_analysis
    return competitor_analysis(req.competitors, req.platform, req.niche)


@router.post("/trends")
async def trends(req: TrendRequest):
    """Trend research."""
    from admin.tools.social_tools import trend_research
    return trend_research(req.niche, req.platform)


@router.post("/engagement")
async def engagement(req: EngagementRequest):
    """Engagement strategy."""
    from admin.tools.social_tools import engagement_strategy
    return engagement_strategy(req.platform, req.goals, req.audience_size)


@router.post("/platform")
async def platform(req: PlatformRequest):
    """Platform strategy."""
    from admin.tools.social_tools import platform_strategy
    return platform_strategy(req.industry, req.goals, req.budget)


@router.post("/gaps")
async def gaps(req: GapRequest):
    """Content gap analysis."""
    from admin.tools.social_tools import content_gap_analysis
    return content_gap_analysis(req.your_content, req.competitor_content, req.niche)


@router.post("/audience")
async def audience(req: AudienceRequest):
    """Audience analysis."""
    from admin.tools.social_tools import audience_analysis
    return audience_analysis(req.industry, req.platform, req.location)


@router.post("/growth")
async def growth(req: GrowthRequest):
    """Growth tactics."""
    from admin.tools.social_tools import growth_tactics
    return growth_tactics(req.current_followers, req.platform, req.niche, req.budget)


@router.post("/caption")
async def caption(req: CaptionRequest):
    """Generate post caption."""
    from admin.tools.social_tools import generate_caption
    return generate_caption(req.topic, req.platform, req.tone, req.audience, req.include_cta)


@router.post("/repurpose")
async def repurpose(req: RepurposeRequest):
    """Repurpose content for multiple platforms."""
    from admin.tools.social_tools import repurpose_content
    return repurpose_content(req.original_content, req.source_platform, req.target_platforms, req.topic)


@router.post("/dm-outreach")
async def dm_outreach(req: DMOutreachRequest):
    """DM outreach templates and strategy."""
    from admin.tools.social_tools import dm_outreach
    return dm_outreach(req.purpose, req.platform, req.target_audience, req.tone)


@router.post("/influencers")
async def influencers(req: InfluencerRequest):
    """Influencer research."""
    from admin.tools.social_tools import influencer_research
    return influencer_research(req.niche, req.platform, req.budget, req.count)


@router.post("/analytics")
async def analytics(req: AnalyticsRequest):
    """Analytics report."""
    from admin.tools.social_tools import analytics_report
    return analytics_report(req.platform, req.metrics, req.period)


@router.post("/request-content")
async def request_content(req: RequestContentRequest):
    """Brief Content Agent for social visuals."""
    from admin.workspace.agents.social import SocialAgent
    agent = SocialAgent(workspace_name=req.workspace_name, client_name=req.workspace_name)
    return agent.request_content(
        content_type=req.content_type,
        topic=req.topic,
        platform=req.platform,
        description=req.description,
        style=req.style,
        priority=req.priority,
        quantity=req.quantity,
    )


@router.get("/tools")
async def list_tools():
    """List available tools."""
    from admin.tools.social_tools import SOCIAL_TOOLS
    return {
        "tools": [
            {"name": t["function"]["name"], "description": t["function"]["description"]}
            for t in SOCIAL_TOOLS
        ],
        "count": len(SOCIAL_TOOLS),
    }
