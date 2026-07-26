"""Website Agent API Routes — Full-stack web developer endpoints.

Endpoints:
  POST /api/website/chat              — Chat with Website Agent (SEO requests auto-route to SEO Agent)
  POST /api/website/analyze           — Analyze website structure + tech stack
  POST /api/website/performance       — Check page performance
  POST /api/website/links             — Find broken links
  POST /api/website/security          — Security headers check
  POST /api/website/accessibility     — a11y checks
  POST /api/website/tech-stack        — Recommend tech stack
  POST /api/website/design-plan       — Plan site architecture
  POST /api/website/competitors       — Scan competitor websites
  POST /api/website/request-content   — Brief Content Agent for visuals
  POST /api/website/request-seo       — Route SEO work to SEO Agent
  GET  /api/website/tools             — Available tools

NOTE: SEO endpoints (/seo, /sitemap) are handled by SEO Agent routes (/api/seo/*).
      Website Agent auto-routes SEO requests to SEO Agent via agent_bus.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/website", tags=["website-agent"])


# ── Request Models ───────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    workspace_name: str = "Default"
    client_name: str = "Client"


class AnalyzeRequest(BaseModel):
    url: str


class PerformanceRequest(BaseModel):
    url: str


class LinksRequest(BaseModel):
    url: str
    max_links: int = 50


class SecurityRequest(BaseModel):
    url: str


class AccessibilityRequest(BaseModel):
    url: str


class TechStackRequest(BaseModel):
    site_type: str = ""
    needs_ecommerce: bool = False
    needs_blog: bool = False
    budget: str = "medium"
    client_preference: str = ""


class DesignPlanRequest(BaseModel):
    site_type: str = "landing"
    pages: str = "home, about, services, contact"
    style: str = "modern"


class CompetitorsRequest(BaseModel):
    urls: list[str]


class RequestContentRequest(BaseModel):
    workspace_name: str = "Default"
    content_type: str = "hero_image"
    topic: str = ""
    description: str = ""
    style: str = "professional"
    priority: str = "normal"


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/chat")
async def chat(req: ChatRequest):
    """Chat with Website Agent."""
    from admin.workspace.agents.website import WebsiteAgent
    agent = WebsiteAgent(workspace_name=req.workspace_name, client_name=req.client_name)
    output, thread_id = await agent.chat(req.message)
    return {"response": output, "thread_id": thread_id}


@router.post("/analyze")
async def analyze(req: AnalyzeRequest):
    """Analyze website: tech stack, structure, navigation, images."""
    from admin.tools.website_tools import analyze_website
    return analyze_website(req.url)


@router.post("/performance")
async def performance(req: PerformanceRequest):
    """Check page performance: load time, size, resources."""
    from admin.tools.website_tools import check_performance
    return check_performance(req.url)


@router.post("/links")
async def links(req: LinksRequest):
    """Find broken links on a page."""
    from admin.tools.website_tools import check_links
    return check_links(req.url, req.max_links)



@router.post("/security")
async def security(req: SecurityRequest):
    """Check security headers."""
    from admin.tools.website_tools import security_check
    return security_check(req.url)


@router.post("/accessibility")
async def accessibility(req: AccessibilityRequest):
    """Accessibility checks."""
    from admin.tools.website_tools import check_accessibility
    return check_accessibility(req.url)


@router.post("/tech-stack")
async def tech_stack(req: TechStackRequest):
    """Recommend tech stack."""
    from admin.tools.website_tools import tech_stack_advisor
    return tech_stack_advisor(
        site_type=req.site_type,
        needs_ecommerce=req.needs_ecommerce,
        needs_blog=req.needs_blog,
        budget=req.budget,
        client_preference=req.client_preference,
    )


@router.post("/design-plan")
async def design_plan(req: DesignPlanRequest):
    """Plan site architecture."""
    from admin.tools.website_tools import design_planner
    return design_planner(
        site_type=req.site_type,
        pages=req.pages,
        style=req.style,
    )


@router.post("/competitors")
async def competitors(req: CompetitorsRequest):
    """Scan competitor websites."""
    from admin.tools.website_tools import competitor_sites
    return competitor_sites(req.urls)



@router.post("/request-content")
async def request_content(req: RequestContentRequest):
    """Brief Content Agent for website visuals."""
    from admin.workspace.agents.website import WebsiteAgent
    agent = WebsiteAgent(workspace_name=req.workspace_name, client_name=req.workspace_name)
    return agent.request_content(
        content_type=req.content_type,
        topic=req.topic,
        description=req.description,
        style=req.style,
        priority=req.priority,
    )


@router.post("/request-seo")
async def request_seo(req: RequestContentRequest):
    """Route SEO work to SEO Agent — SEO Agent karega kaam aur report dega."""
    from admin.workspace.agents.seo import SEOAgent
    seo_agent = SEOAgent(workspace_name=req.workspace_name, client_name=req.workspace_name)
    
    task = req.topic or req.description
    if not task:
        raise HTTPException(400, "topic or description required for SEO task")
    
    response, phases = await seo_agent.chat(message=task)
    
    # Also send brief via agent_bus for audit trail
    from admin.workspace.agent_bus import send_message
    send_message(
        from_agent="website",
        to_agent="seo",
        workspace_id=req.workspace_name,
        subject=f"SEO task from Website Agent: {task[:80]}",
        content=response,
        message_type="response",
    )
    
    return {
        "status": "completed",
        "routed_to": "seo",
        "task": task[:200],
        "response": response,
        "thinking_phases": phases,
    }


@router.get("/tools")
async def list_tools():
    """List available tools."""
    from admin.tools.website_tools import WEBSITE_TOOLS
    return {
        "tools": [
            {"name": t["function"]["name"], "description": t["function"]["description"]}
            for t in WEBSITE_TOOLS
        ],
        "count": len(WEBSITE_TOOLS),
        "seo_routing": "SEO requests are routed to SEO Agent",
    }
