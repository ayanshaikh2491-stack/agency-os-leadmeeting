"""Content Agent API Routes — Full-Spectrum Content Endpoints.

Content Agent creates images, videos, AND text content.

Endpoints:
  POST /api/content/chat             — Chat with content agent (LangGraph)
  POST /api/content/discover-brand   — Auto-discover client brand identity
  POST /api/content/parse-brief      — Parse a visual brief from domain agent
  POST /api/content/plan             — Plan visual production
  POST /api/content/generate-image   — Generate AI image via FLUX/Kaggle
  POST /api/content/generate-video   — Generate AI video via CogVideoX/Kaggle
  POST /api/content/generate-ad      — Generate ad creative image
  POST /api/content/generate-social  — Generate social media image
  POST /api/content/generate-hero    — Generate hero/banner image
  POST /api/content/batch-generate   — Batch generate images
  POST /api/content/brief-content-agent — Domain agent briefs Content Agent via agent_bus

  Text Content Tools:
  POST /api/content/analyze-readability     — Analyze content readability
  POST /api/content/content-brief           — Generate content brief
  POST /api/content/blog-post               — Generate SEO blog post
  POST /api/content/optimize-meta           — Optimize meta descriptions
  POST /api/content/rewrite                 — Rewrite content for clarity
  POST /api/content/calendar                — Generate content calendar
  POST /api/content/gap-analysis            — Analyze content gaps vs competitors
  POST /api/content/search-images           — Search free stock images
  POST /api/content/image-specs             — Get social image size specs
  POST /api/content/repurpose               — Repurpose content across platforms
  POST /api/content/ad-copy                 — Generate ad copy

  Agency Level:
  GET  /api/content/agency/stats            — Agency content stats
  GET  /api/content/agency/knowledge        — Get cross-project knowledge
  GET  /api/content/agency/best-prompts     — Get best prompt patterns

  Job Queue (On-Demand GPU):
  POST /api/content/queue/submit            — Submit job to GPU queue
  GET  /api/content/queue/status/{job_id}   — Check job status
  GET  /api/content/queue/list              — List all jobs in queue
  GET  /api/content/queue/overview          — Queue overview (pending/running/done)
  POST /api/content/queue/process           — Process next job (called by worker)

  System:
  GET  /api/content/tools            — List all available tools
  GET  /api Content Agent status
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
    brief_from: str = ""  # Which agent sent the brief


class DiscoverBrandRequest(BaseModel):
    website_url: str


class ParseBriefRequest(BaseModel):
    brief_text: str


class PlanProductionRequest(BaseModel):
    brief: dict[str, Any]
    brand_identity: dict[str, Any] | None = None


class GenerateImageRequest(BaseModel):
    prompt: str
    width: int = 1024
    height: int = 1024
    steps: int = 20


class GenerateVideoRequest(BaseModel):
    prompt: str
    frames: int = 49


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


class BatchGenerateRequest(BaseModel):
    topics: list[str]
    platform: str = "instagram"


class BriefContentAgentRequest(BaseModel):
    """Domain agent briefs Content Agent via agent_bus."""
    from_agent: str  # seo, ads, social, website
    workspace_id: str
    task: str
    context: str = ""
    priority: str = "normal"
    client_website_url: str | None = None  # For brand discovery


# ── Text Content Request Models ──────────────────────────────────────────────


class ReadabilityRequest(BaseModel):
    url: str


class ContentBriefRequest(BaseModel):
    topic: str
    target_audience: str = "general"
    word_count: int = 1500


class BlogPostRequest(BaseModel):
    topic: str
    keywords: list[str] | None = None
    word_count: int = 1500


class OptimizeMetaRequest(BaseModel):
    url: str


class RewriteRequest(BaseModel):
    text: str
    style: str = "professional"


class CalendarRequest(BaseModel):
    niche: str
    weeks: int = 4


class GapAnalysisRequest(BaseModel):
    url: str
    competitors: list[str] | None = None


class SearchImagesRequest(BaseModel):
    query: str
    count: int = 5


class ImageSpecsRequest(BaseModel):
    platform: str = "all"


class RepurposeRequest(BaseModel):
    content: str
    platform: str = "instagram"


class AdCopyRequest(BaseModel):
    product: str
    platform: str = "facebook"


class AgencyKnowledgeRequest(BaseModel):
    industry: str = ""
    platform: str = ""
    visual_type: str = ""


class BestPromptsRequest(BaseModel):
    visual_type: str = ""
    platform: str = ""
    top_n: int = 5


# ── Visual Content Endpoints ─────────────────────────────────────────────────


@router.get("/tools")
async def list_tools():
    """List all tools available to Content Agent."""
    from admin.tools.visual_tools import VISUAL_TOOLS
    from admin.tools.content_tools import CONTENT_TOOLS
    return {
        "visual_tools": [t["function"]["name"] for t in VISUAL_TOOLS],
        "content_tools": [t["name"] for t in CONTENT_TOOLS],
        "total_tools": len(VISUAL_TOOLS) + len(CONTENT_TOOLS),
        "categories": {
            "visual_generation": ["discover_brand_identity", "generate_image_kaggle",
                                  "generate_video_kaggle", "generate_ad_image",
                                  "generate_social_image", "generate_hero_image",
                                  "batch_generate_images", "generate_video_ad"],
            "text_content": ["analyze_readability", "generate_content_brief",
                            "generate_blog_post", "optimize_meta_descriptions",
                            "rewrite_content", "generate_content_calendar",
                            "analyze_content_gaps"],
            "social": ["search_images", "get_social_image_specs",
                      "repurpose_for_social", "generate_ad_copy"],
            "planning": ["parse_visual_brief", "plan_visual_production"],
        },
    }


@router.get("/status")
async def content_status():
    """Content Agent status and capabilities."""
    return {
        "agent": "Content Agent",
        "type": "Full-Spectrum Content Execution Engine",
        "scope": "images, videos, graphics, text content, strategy, optimization",
        "compute": "Kaggle API (FLUX for images, CogVideoX for videos)",
        "gpu_quota": "30 hrs/week free on Kaggle",
        "capabilities": {
            "visual_content": True,
            "text_content": True,
            "brand_discovery": True,
            "content_strategy": True,
            "seo_optimization": True,
            "social_repurposing": True,
            "cross_project_learning": True,
        },
        "interview_compliance": {
            "Q1_full_spectrum": True,
            "Q2_full_spectrum": True,
            "Q3_kaggle_api": True,
            "Q4_per_workspace": True,
            "Q5_brand_discovery": True,
            "Q6_domain_approval": True,
            "Q7_cross_learning": True,
        },
    }


@router.post("/chat")
async def content_chat(body: ChatRequest):
    """Chat with Content Agent — receives briefs, creates visuals + text."""
    from admin.workspace.agents.content import ContentAgent

    agent = ContentAgent(
        workspace_name=body.workspace_name,
        client_name=body.client_name,
    )

    response, thinking_phases = await agent.chat(
        message=body.message,
        brief_from=body.brief_from,
    )

    return {
        "success": True,
        "response": response,
        "thinking_phases": thinking_phases,
        "workspace": body.workspace_name,
        "client": body.client_name,
    }


@router.post("/discover-brand")
async def discover_brand(body: DiscoverBrandRequest):
    """Auto-discover client brand identity from their website."""
    from admin.tools.visual_tools import discover_brand_identity
    return {"success": True, "data": discover_brand_identity(body.website_url)}


@router.post("/parse-brief")
async def parse_brief(body: ParseBriefRequest):
    """Parse a visual brief from a domain agent."""
    from admin.tools.visual_tools import parse_visual_brief
    return {"success": True, "data": parse_visual_brief(body.brief_text)}


@router.post("/plan")
async def plan_production(body: PlanProductionRequest):
    """Plan visual production with prompts, dimensions, GPU estimate."""
    from admin.tools.visual_tools import plan_visual_production
    return {
        "success": True,
        "data": plan_visual_production(body.brief, body.brand_identity),
    }


@router.post("/generate-image")
async def generate_image(body: GenerateImageRequest):
    """Generate AI image via FLUX on Kaggle GPU."""
    from admin.tools.kaggle_tools import generate_image_kaggle
    return {
        "success": True,
        "data": generate_image_kaggle(body.prompt, body.width, body.height, body.steps),
    }


@router.post("/generate-video")
async def generate_video(body: GenerateVideoRequest):
    """Generate AI video via CogVideoX on Kaggle GPU."""
    from admin.tools.kaggle_tools import generate_video_kaggle
    return {"success": True, "data": generate_video_kaggle(body.prompt, body.frames)}


@router.post("/generate-ad")
async def generate_ad(body: GenerateAdRequest):
    """Generate ad creative image sized for specific platform."""
    from admin.tools.kaggle_tools import generate_ad_image
    return {
        "success": True,
        "data": generate_ad_image(body.product, body.platform, body.style),
    }


@router.post("/generate-social")
async def generate_social(body: GenerateSocialRequest):
    """Generate social media post image."""
    from admin.tools.kaggle_tools import generate_social_image
    return {
        "success": True,
        "data": generate_social_image(body.topic, body.platform),
    }


@router.post("/generate-hero")
async def generate_hero(body: GenerateHeroRequest):
    """Generate hero/banner image for website or blog."""
    from admin.tools.kaggle_tools import generate_hero_image
    return {"success": True, "data": generate_hero_image(body.topic, body.style)}


@router.post("/batch-generate")
async def batch_generate(body: BatchGenerateRequest):
    """Batch generate images for content calendar."""
    from admin.tools.kaggle_tools import batch_generate_images
    return {
        "success": True,
        "data": batch_generate_images(body.topics, body.platform),
    }


# ── Text Content Endpoints ───────────────────────────────────────────────────


@router.post("/analyze-readability")
async def analyze_readability(body: ReadabilityRequest):
    """Analyze content readability with Flesch-Kincaid scores."""
    from admin.tools.content_tools import analyze_readability
    return {"success": True, "data": analyze_readability(body.url)}


@router.post("/content-brief")
async def content_brief(body: ContentBriefRequest):
    """Generate a content brief with outline, keywords, and structure."""
    from admin.tools.content_tools import generate_content_brief
    return {
        "success": True,
        "data": generate_content_brief(body.topic, body.target_audience, body.word_count),
    }


@router.post("/blog-post")
async def blog_post(body: BlogPostRequest):
    """Generate an SEO-optimized blog post with HTML output."""
    from admin.tools.content_tools import generate_blog_post
    return {
        "success": True,
        "data": generate_blog_post(body.topic, body.keywords, body.word_count),
    }


@router.post("/optimize-meta")
async def optimize_meta(body: OptimizeMetaRequest):
    """Analyze and suggest optimized meta descriptions."""
    from admin.tools.content_tools import optimize_meta_descriptions
    return {"success": True, "data": optimize_meta_descriptions(body.url)}


@router.post("/rewrite")
async def rewrite(body: RewriteRequest):
    """Rewrite content for better readability and clarity."""
    from admin.tools.content_tools import rewrite_content
    return {"success": True, "data": rewrite_content(body.text, body.style)}


@router.post("/calendar")
async def calendar(body: CalendarRequest):
    """Generate a weekly content calendar."""
    from admin.tools.content_tools import generate_content_calendar
    return {"success": True, "data": generate_content_calendar(body.niche, body.weeks)}


@router.post("/gap-analysis")
async def gap_analysis(body: GapAnalysisRequest):
    """Analyze content gaps vs competitors."""
    from admin.tools.content_tools import analyze_content_gaps
    return {
        "success": True,
        "data": analyze_content_gaps(body.url, body.competitors),
    }


@router.post("/search-images")
async def search_images(body: SearchImagesRequest):
    """Search free stock images from Unsplash."""
    from admin.tools.content_tools import search_images
    return {"success": True, "data": search_images(body.query, body.count)}


@router.post("/image-specs")
async def image_specs(body: ImageSpecsRequest):
    """Get image size specifications for social media platforms."""
    from admin.tools.content_tools import get_social_image_specs
    return {"success": True, "data": get_social_image_specs(body.platform)}


@router.post("/repurpose")
async def repurpose(body: RepurposeRequest):
    """Repurpose content across social media platforms."""
    from admin.tools.content_tools import repurpose_for_social
    return {"success": True, "data": repurpose_for_social(body.content, body.platform)}


@router.post("/ad-copy")
async def ad_copy(body: AdCopyRequest):
    """Generate ad copy for different platforms."""
    from admin.tools.content_tools import generate_ad_copy
    return {"success": True, "data": generate_ad_copy(body.product, body.platform)}


# ── Agency-Level Endpoints ───────────────────────────────────────────────────


@router.get("/agency/stats")
async def agency_stats():
    """Get agency-level content stats (cross-project)."""
    from admin.agency.content_agent import get_agency_content_agent
    agent = get_agency_content_agent()
    return {"success": True, "data": agent.get_stats()}


@router.post("/agency/knowledge")
async def agency_knowledge(body: AgencyKnowledgeRequest):
    """Get accumulated cross-project knowledge for a workspace."""
    from admin.agency.content_agent import get_agency_content_agent
    agent = get_agency_content_agent()
    return {
        "success": True,
        "data": agent.get_knowledge_for_workspace(
            industry=body.industry,
            platform=body.platform,
            visual_type=body.visual_type,
        ),
    }


@router.post("/agency/best-prompts")
async def agency_best_prompts(body: BestPromptsRequest):
    """Get best-performing prompt patterns from cross-project data."""
    from admin.agency.content_agent import get_agency_content_agent
    agent = get_agency_content_agent()
    return {
        "success": True,
        "data": agent.get_best_prompts(
            visual_type=body.visual_type,
            platform=body.platform,
            top_n=body.top_n,
        ),
    }


# ── Domain Agent Briefing Endpoint ───────────────────────────────────────────


@router.post("/brief-content-agent")
async def brief_content_agent(body: BriefContentAgentRequest):
    """Domain agent briefs Content Agent via agent_bus.

    Flow (Interview Q6):
      1. Domain agent sends visual brief
      2. Content Agent receives via agent_bus
      3. Content Agent creates visuals + text
      4. Content Agent responds to briefing agent
      5. Briefing agent approves output
    """
    from admin.workspace.agent_bus import brief_agent

    # Step 1: Send brief via agent_bus
    msg = brief_agent(
        from_agent=body.from_agent,
        to_agent="content",
        workspace_id=body.workspace_id,
        task=body.task,
        context=body.context,
        priority=body.priority,
    )

    # Step 2: Auto-discover brand if website URL provided
    brand_data = None
    if body.client_website_url:
        from admin.tools.visual_tools import discover_brand_identity
        brand_data = discover_brand_identity(body.client_website_url)

    # Step 3: Run Content Agent with the brief
    from admin.workspace.agents.content import ContentAgent

    agent = ContentAgent(workspace_name=body.workspace_id)
    brief_with_context = body.task
    if brand_data and brand_data.get("brand_name"):
        brief_with_context += f"\n\nClient brand: {brand_data['brand_name']}"
        brief_with_context += f"\nBrand colors: {', '.join(brand_data.get('colors', []))}"
        brief_with_context += f"\nVisual style: {brand_data.get('visual_style', 'unknown')}"

    response, thinking_phases = await agent.chat(
        message=brief_with_context,
        brief_from=body.from_agent,
    )

    # Step 4: Store output for domain agent review (Interview Q6)
    from admin.workspace.manager import store_agent_output
    store_agent_output(
        workspace_id=body.workspace_id,
        agent_type="content",
        task=body.task,
        output=response,
    )

    return {
        "success": True,
        "brief_id": msg.id,
        "brief_from": body.from_agent,
        "response": response,
        "thinking_phases": thinking_phases,
        "brand_discovered": brand_data is not None,
        "brand_name": brand_data.get("brand_name", "") if brand_data else "",
        "approval_note": f"{body.from_agent} agent must approve this output",
    }


# ── Job Queue Endpoints (On-Demand GPU) ──────────────────────────────────────


class QueueSubmitRequest(BaseModel):
    """Domain agent submits a structured brief to the GPU queue."""
    workspace_id: str
    from_agent: str  # social, ads, website, seo
    content_type: str  # image, video, ad_creative, social_post, hero_banner, infographic
    platform: str = "instagram"
    style: str = "professional"
    quantity: int = 1
    topic: str = ""
    description: str = ""  # Detailed description of what to create
    text_overlay: str = ""
    cta: str = ""
    reference_urls: list[str] = []
    priority: str = "normal"


class QueueProcessRequest(BaseModel):
    """Worker calls this to process the next job in queue."""
    workspace_id: str


@router.post("/queue/submit")
async def queue_submit(body: QueueSubmitRequest):
    """Submit a structured brief to the GPU queue.

    Domain Agent sends: WHAT to create (topic, platform, style, quantity)
    Content Agent enhances: HOW to create it (brand colors, AI prompts, dimensions)
    GPU processes: WHEN it's free (on-demand, no waste)
    """
    from admin.tools.content_queue import ContentBrief, enhance_brief, get_queue
    from admin.workspace.manager import get_workspace

    # Build brief from domain agent's request
    brief = ContentBrief(
        workspace_id=body.workspace_id,
        from_agent=body.from_agent,
        content_type=body.content_type,
        platform=body.platform,
        style=body.style,
        quantity=body.quantity,
        topic=body.topic,
        description=body.description,
        text_overlay=body.text_overlay,
        cta=body.cta,
        reference_urls=body.reference_urls,
        priority=body.priority,
    )

    # Get client context from workspace
    ws = get_workspace(body.workspace_id)
    client_context = ws.client_context if ws and hasattr(ws, 'client_context') and ws.client_context else {}

    # Content Agent enhances the brief (ITS BRAIN WORKS HERE)
    brief = enhance_brief(brief, client_context)

    # Add to GPU queue
    queue = get_queue(body.workspace_id)
    job_id = queue.submit(brief)

    return {
        "success": True,
        "job_id": job_id,
        "status": "pending",
        "enhanced_prompt": brief.enhanced_prompt,
        "dimensions": f"{brief.width}x{brief.height}",
        "ai_reasoning": brief.ai_reasoning,
        "style_enhancement": brief.style_enhancement,
        "brand_colors_used": brief.brand_colors_used,
        "queue_position": len(queue._queue),
        "gpu_busy": queue._running_job is not None,
        "message": f"Job queued. GPU will process when free. Queue depth: {len(queue._queue)}",
    }


@router.get("/queue/status/{job_id}")
async def queue_status(job_id: str, workspace_id: str = ""):
    """Check status of a specific job."""
    from admin.tools.content_queue import get_queue

    # Try to find in all queues if workspace_id not provided
    if workspace_id:
        queue = get_queue(workspace_id)
        status = queue.get_status(job_id)
        if status:
            return {"success": True, "data": status}
    else:
        from admin.tools.content_queue import _queues
        for q in _queues.values():
            status = q.get_status(job_id)
            if status:
                return {"success": True, "data": status}

    raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")


@router.get("/queue/list")
async def queue_list(workspace_id: str = "", limit: int = 10):
    """List recent jobs in queue."""
    from admin.tools.content_queue import get_queue, _queues

    if workspace_id:
        queue = get_queue(workspace_id)
        return {"success": True, "data": queue.list_recent(limit)}
    else:
        all_jobs = []
        for q in _queues.values():
            all_jobs.extend(q.list_recent(limit))
        all_jobs.sort(key=lambda j: j.get("created_at", ""), reverse=True)
        return {"success": True, "data": all_jobs[:limit]}


@router.get("/queue/overview")
async def queue_overview(workspace_id: str = ""):
    """Get queue overview — pending, running, completed, failed."""
    from admin.tools.content_queue import get_queue, _queues

    if workspace_id:
        queue = get_queue(workspace_id)
        return {"success": True, "data": queue.get_queue_status()}
    else:
        overviews = []
        for q in _queues.values():
            overviews.append(q.get_queue_status())
        return {"success": True, "data": overviews}


@router.post("/queue/process")
async def queue_process(body: QueueProcessRequest):
    """Process the next job in the GPU queue.

    Called by a worker (cron job or background process).
    Picks the next pending job, runs GPU generation, saves output.
    """
    from admin.tools.content_queue import get_queue, JobStatus
    from admin.tools.kaggle_tools import generate_image_kaggle, generate_video_kaggle

    queue = get_queue(body.workspace_id)
    job = queue.get_next()

    if not job:
        return {
            "success": True,
            "message": "No jobs to process",
            "queue_status": queue.get_queue_status(),
        }

    try:
        # Execute based on content type
        if job.content_type == "video":
            result = generate_video_kaggle(
                prompt=job.enhanced_prompt,
                frames=job.frames,
            )
        else:
            result = generate_image_kaggle(
                prompt=job.enhanced_prompt,
                width=job.width,
                height=job.height,
                steps=job.steps,
            )

        # Check result
        if result.get("status") in ("notebook_ready", "submitted", "ready"):
            # Success — save output info
            output_dir = _OUTPUT_BASE / body.workspace_id / job.job_id
            output_dir.mkdir(parents=True, exist_ok=True)

            # Save job metadata
            meta_file = output_dir / "job.json"
            meta_file.write_text(
                json.dumps({
                    "job_id": job.job_id,
                    "from_agent": job.from_agent,
                    "content_type": job.content_type,
                    "platform": job.platform,
                    "enhanced_prompt": job.enhanced_prompt,
                    "dimensions": f"{job.width}x{job.height}",
                    "result": result,
                }, indent=2, default=str),
                encoding="utf-8",
            )

            output_files = [str(meta_file)]
            if result.get("notebook_code"):
                nb_file = output_dir / "notebook.ipynb"
                nb_file.write_text(result["notebook_code"], encoding="utf-8")
                output_files.append(str(nb_file))

            queue.complete(job.job_id, output_files, str(output_dir))

            return {
                "success": True,
                "job_id": job.job_id,
                "status": "completed",
                "output_dir": str(output_dir),
                "result": result,
                "queue_status": queue.get_queue_status(),
            }
        else:
            # Failed
            error = result.get("error", result.get("message", "Unknown error"))
            will_retry = queue.fail(job.job_id, error)
            return {
                "success": False,
                "job_id": job.job_id,
                "status": "retrying" if will_retry else "failed",
                "error": error,
                "retry_count": job.retry_count,
                "queue_status": queue.get_queue_status(),
            }

    except Exception as e:
        logger.exception("Job processing failed: %s", job.job_id)
        queue.fail(job.job_id, str(e))
        return {
            "success": False,
            "job_id": job.job_id,
            "status": "failed",
            "error": str(e)[:200],
            "queue_status": queue.get_queue_status(),
        }


# ── Content Agent Intelligence Endpoints ──────────────────────────────────────


class BrandDiscoverRequest(BaseModel):
    """Auto-discover brand identity from client website."""
    workspace_id: str


@router.post("/agent/brand-discover")
async def agent_brand_discover(body: BrandDiscoverRequest):
    """Auto-discover client brand from their website.

    Called automatically on first brief if brand info is missing.
    Updates workspace client_context with discovered colors, style, etc.
    """
    from admin.workspace.manager import get_workspace
    from admin.workspace.agents.content import ContentAgent

    ws = get_workspace(body.workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    agent = ContentAgent(
        workspace_name=ws.name,
        client_name=ws.client_name,
        client_context=ws.client_context or {},
        workspace_id=body.workspace_id,
    )

    result = await agent.auto_discover_brand()
    return {"success": True, "data": result}


class SubmitJobRequest(BaseModel):
    """Submit a visual job through the Content Agent (with intelligence)."""
    workspace_id: str
    brief_from: str = ""
    content_type: str
    platform: str = "instagram"
    topic: str = ""
    style: str = "professional"
    quantity: int = 1
    priority: str = "normal"
    description: str = ""
    text_overlay: str = ""
    cta: str = ""


@router.post("/agent/submit-job")
async def agent_submit_job(body: SubmitJobRequest):
    """Submit a visual content job through the Content Agent.

    Content Agent enhances the brief with brand intelligence before queuing.
    """
    from admin.workspace.manager import get_workspace
    from admin.workspace.agents.content import ContentAgent

    ws = get_workspace(body.workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    agent = ContentAgent(
        workspace_name=ws.name,
        client_name=ws.client_name,
        client_context=ws.client_context or {},
        workspace_id=body.workspace_id,
    )

    result = agent.submit_visual_job(
        brief_from=body.brief_from,
        content_type=body.content_type,
        platform=body.platform,
        topic=body.topic,
        style=body.style,
        quantity=body.quantity,
        priority=body.priority,
        description=body.description,
        text_overlay=body.text_overlay,
        cta=body.cta,
    )

    return {"success": True, "data": result}


class ProcessJobRequest(BaseModel):
    """Process the next job in workspace queue."""
    workspace_id: str


@router.post("/agent/process-job")
async def agent_process_job(body: ProcessJobRequest):
    """Process the next queued job through the Content Agent.

    Routes to appropriate tool (image/video) based on content type.
    Handles retry on failure.
    """
    from admin.workspace.manager import get_workspace
    from admin.workspace.agents.content import ContentAgent

    ws = get_workspace(body.workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    agent = ContentAgent(
        workspace_name=ws.name,
        client_name=ws.client_name,
        client_context=ws.client_context or {},
        workspace_id=body.workspace_id,
    )

    result = await agent.process_next_job()

    if result is None:
        return {"success": True, "message": "No jobs in queue", "data": None}

    return {"success": True, "data": result}


@router.get("/agent/memory/{workspace_id}")
async def agent_memory(workspace_id: str):
    """Get workspace Content Agent memory summary.

    Shows success rate, brand learnings, mistakes to avoid, platform performance.
    """
    from admin.workspace.manager import get_workspace
    from admin.workspace.agents.content import ContentAgent

    ws = get_workspace(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    agent = ContentAgent(
        workspace_name=ws.name,
        client_name=ws.client_name,
        client_context=ws.client_context or {},
        workspace_id=workspace_id,
    )

    memory = agent.get_memory_summary()
    stats = agent.get_stats()

    return {
        "success": True,
        "data": {
            "memory_summary": memory,
            "stats": stats,
        },
    }


@router.get("/agent/queue-status/{workspace_id}")
async def agent_queue_status(workspace_id: str):
    """Get Content Agent queue status for a workspace."""
    from admin.workspace.manager import get_workspace
    from admin.workspace.agents.content import ContentAgent

    ws = get_workspace(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    agent = ContentAgent(
        workspace_name=ws.name,
        client_name=ws.client_name,
        client_context=ws.client_context or {},
        workspace_id=workspace_id,
    )

    status = agent.get_queue_status()
    recent = agent.list_recent_jobs(5)

    return {
        "success": True,
        "data": {
            "queue": status,
            "recent_jobs": recent,
        },
    }


class ApprovalRequest(BaseModel):
    """Request CEO approval for content."""
    workspace_id: str
    content_type: str
    output_summary: str
    brief_from: str = ""
    output_files: list[str] = []


@router.post("/agent/approve")
async def agent_request_approval(body: ApprovalRequest):
    """Request CEO approval for content before publishing.

    Stores content in pending reviews for CEO to approve/reject.
    """
    from admin.workspace.manager import get_workspace
    from admin.workspace.agents.content import ContentAgent

    ws = get_workspace(body.workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    agent = ContentAgent(
        workspace_name=ws.name,
        client_name=ws.client_name,
        client_context=ws.client_context or {},
        workspace_id=body.workspace_id,
    )

    result = agent.request_approval(
        content_type=body.content_type,
        output_summary=body.output_summary,
        brief_from=body.brief_from,
        output_files=body.output_files,
    )

    return {"success": True, "data": result}
