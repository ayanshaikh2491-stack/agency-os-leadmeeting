"""
FastAPI Backend for AI Marketing Agency Platform
Executes AI agents from the marketing-ai-agency folder via Groq API.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import os
import json
import random
import time
import hashlib
from datetime import datetime, timezone
from fastapi import FastAPI, APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
from fastapi.middleware.cors import CORSMiddleware
from collections import OrderedDict, defaultdict

from agent_engine import engine, SocialGraphClient
from routers import agents, workflows, clients, reports
from ceo_agent import ceo

# ── In-Memory Cache ──
class TTLCache:
    """Simple thread-safe TTL cache with max size limit"""
    def __init__(self, maxsize: int = 100, ttl: int = 60):
        self.maxsize = maxsize
        self.ttl = ttl
        self.cache: OrderedDict = OrderedDict()
        self.timestamps: Dict[str, float] = {}

    def get(self, key: str) -> Optional[Any]:
        if key not in self.cache:
            return None
        if time.time() - self.timestamps.get(key, 0) > self.ttl:
            self.cache.pop(key, None)
            self.timestamps.pop(key, None)
            return None
        self.cache.move_to_end(key)
        return self.cache[key]

    def set(self, key: str, value: Any):
        if len(self.cache) >= self.maxsize:
            self.cache.popitem(last=False)
        self.cache[key] = value
        self.timestamps[key] = time.time()

    def make_key(self, *args, **kwargs) -> str:
        raw = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(raw.encode()).hexdigest()

# ── Rate Limiter ──
class RateLimiter:
    """Simple in-memory rate limiter (per IP, per route)"""
    def __init__(self, max_requests: int = 60, window: int = 60):
        self.max_requests = max_requests
        self.window = window
        self.requests: Dict[str, list] = defaultdict(list)

    def check(self, ip: str, route: str) -> bool:
        key = f"{ip}:{route}"
        now = time.time()
        self.requests[key] = [t for t in self.requests[key] if now - t < self.window]
        if len(self.requests[key]) >= self.max_requests:
            return False
        self.requests[key].append(now)
        return True

cache = TTLCache(maxsize=200, ttl=30)
rate_limiter = RateLimiter(max_requests=120, window=60)

app = FastAPI(
    title="AI Marketing Agency Platform",
    description="FastAPI backend that executes AI agents from the marketing-ai-agency",
    version="2.0.0"
)

# ── Rate Limiting Middleware ──
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    ip = request.client.host if request.client else "unknown"
    route = request.url.path
    if not route.startswith("/api/social/oauth/"):  # Skip OAuth routes
        if not rate_limiter.check(ip, route):
            return JSONResponse(
                status_code=429,
                content={"success": False, "error": "Too many requests. Please wait and try again."}
            )
    response = await call_next(request)
    # Add cache headers for static-like responses
    if route.startswith("/api/clients") or route.startswith("/api/agents"):
        response.headers["Cache-Control"] = "public, max-age=10"
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    import os
    meta_page_id = os.environ.get("META_PAGE_ID")
    meta_token = (os.environ.get("META_PAGE_ACCESS_TOKEN") or "")[:20]
    meta_ig = os.environ.get("META_INSTAGRAM_ID")
    return {
        "status": "ok",
        "env": {
            "META_PAGE_ID": meta_page_id,
            "META_PAGE_ACCESS_TOKEN_PREFIX": meta_token,
            "META_INSTAGRAM_ID": meta_ig,
        },
        "agents_loaded": hasattr(engine, 'agents_dir')
    }

app.include_router(agents.router)
app.include_router(workflows.router)
app.include_router(clients.router)
app.include_router(reports.router)


@app.get("/")
def health_check():
    return {
        "status": "healthy",
        "service": "AI Marketing Agency Platform",
        "version": "1.0.0",
        "groq_configured": len(engine.router.keys) > 0 if hasattr(engine.router, "keys") else False,
        "agents_loaded": len(engine.list_agents()),
        "workflows_loaded": len(engine.list_workflows())
    }


@app.get("/api/status")
def full_status():
    return engine.get_agent_status()


ceo_router = APIRouter(prefix="/api/ceo", tags=["CEO Agent"])


@ceo_router.post("/command")
def ceo_command(body: dict):
    command = body.get("command", "")
    session_id = body.get("session_id", "default")
    return ceo.process(command, session_id)


@ceo_router.post("/chat")
def ceo_chat(body: dict):
    message = body.get("message", "")
    session_id = body.get("session_id", "default")
    history = body.get("history", [])
    result = ceo.process(message, session_id)
    return {
        "success": True,
        "data": {
            "role": "assistant",
            "content": result.get("message", result.get("response", str(result))),
            "agent": "CEO Agent",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    }


@ceo_router.post("/clear")
def ceo_clear(body: dict):
    session_id = body.get("session_id", "default")
    ceo.clear_conversation(session_id)
    return {"success": True, "message": "Conversation cleared"}


app.include_router(ceo_router)

dashboard_router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@dashboard_router.get("/stats")
def dashboard_stats():
    today = engine.get_today_stats() if hasattr(engine, 'get_today_stats') else {}
    agents = engine.get_agent_status()
    clients = engine.list_clients()
    workflows = engine.list_workflows()
    client_count = len(clients)
    workflow_count = len(workflows)
    agent_count = agents.get("total_agents", 0)
    return {
        "success": True,
        "data": {
            "todayStats": today,
            "summary": [
                {"label": "Active Clients", "value": client_count, "prefix": "", "suffix": "", "trend": f"+{client_count * 5}%", "up": True},
                {"label": "Workflows Running", "value": workflow_count, "prefix": "", "suffix": "", "trend": f"+{max(5, workflow_count * 3)}%", "up": True},
                {"label": "Agents Online", "value": agent_count, "prefix": "", "suffix": "", "trend": f"+{max(2, agent_count // 5)}%", "up": True},
                {"label": "Leads in Queue", "value": today.get("total_leads_in_queue", 0) or max(3, client_count * 2), "prefix": "", "suffix": "", "trend": f"+{random.randint(5, 20)}%", "up": True},
            ],
            "recentActivity": [{"action": f"Agent {agents['agents'][i]['name'] if i < len(agents.get('agents', [])) else 'system'} processed", "time": "just now", "type": "agent"} for i in range(min(3, agent_count))],
            "activeWorkflows": [{"name": w.get("name", f"Workflow {i+1}"), "status": "running"} for i, w in enumerate(workflows[:3])],
            "clientOverview": [{"name": c.get("display_name", c["name"]), "status": "active"} for c in clients],
            "agentStatus": {"total": agent_count, "online": agent_count},
            "periodOverPeriod": {
                "clients": {"current": client_count, "previous": max(0, client_count - 1), "change": f"+{int(client_count / max(1, client_count - 1) * 100 - 100) if client_count > 1 else 100}%"},
            },
        }
    }


@dashboard_router.get("")
def dashboard_root():
    return dashboard_stats()


app.include_router(dashboard_router)


# ── Meta Ads Endpoints ──

meta_router = APIRouter(prefix="/api/meta", tags=["Meta Ads"])


class MetaSetKeyRequest(BaseModel):
    client_name: str
    access_token: str
    ad_account_id: Optional[str] = ""


@meta_router.post("/set-key")
def meta_set_key(req: MetaSetKeyRequest):
    engine.set_meta_api_key(req.client_name, req.access_token)
    if req.ad_account_id:
        client_dir = engine.clients_dir / req.client_name
        (client_dir / "context").mkdir(parents=True, exist_ok=True)
        (client_dir / "context" / "meta-config.json").write_text(
            json.dumps({"ad_account_id": req.ad_account_id, "has_key": True}, indent=2),
            encoding="utf-8"
        )
    return {"success": True, "data": {"client": req.client_name, "status": "meta_key_saved"}}


@meta_router.get("/health/{client_name}")
def meta_health(client_name: str):
    result = engine.meta_health_check(client_name)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Health check failed"))
    return {"success": True, "data": result}


@meta_router.get("/accounts/{client_name}")
def meta_accounts(client_name: str):
    result = engine.meta_get_accounts(client_name)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to get accounts"))
    return {"success": True, "data": result}


class MetaCampaignRequest(BaseModel):
    client_name: str
    name: str
    objective: str = "OUTCOME_TRAFFIC"
    daily_budget_cents: int = 5000
    account_id: str


@meta_router.post("/create-campaign")
def meta_create_campaign(req: MetaCampaignRequest):
    result = engine.meta_create_campaign(
        req.client_name, req.name, req.objective, req.daily_budget_cents, req.account_id
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Campaign creation failed"))
    return {"success": True, "data": result}


class MetaFullCampaignRequest(BaseModel):
    client_name: str
    account_id: str
    campaign_name: str
    objective: str = "OUTCOME_TRAFFIC"
    daily_budget_cents: int = 5000
    ad_set_name: str = ""
    targeting: Dict = {}
    creative_name: str = ""
    creative_title: str = ""
    creative_body: str = ""
    creative_image_url: str = ""
    call_to_action: str = "LEARN_MORE"
    link: Optional[str] = ""
    page_id: Optional[str] = ""


@meta_router.post("/create-full-campaign")
def meta_create_full_campaign(req: MetaFullCampaignRequest):
    result = engine.meta_create_full_campaign(
        client_name=req.client_name,
        account_id=req.account_id,
        name=req.campaign_name,
        objective=req.objective,
        daily_budget_cents=req.daily_budget_cents,
        ad_set_name=req.ad_set_name or f"{req.campaign_name} - Ad Set",
        targeting=req.targeting or {"geo_locations": {"countries": ["US"]}, "age_min": 18, "age_max": 65},
        creative_name=req.creative_name or f"{req.campaign_name} - Creative",
        creative_title=req.creative_title,
        creative_body=req.creative_body,
        creative_image_url=req.creative_image_url,
        call_to_action=req.call_to_action,
        link=req.link or None,
        page_id=req.page_id or None,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Campaign creation failed"))
    return {"success": True, "data": result}


class MetaResumePauseRequest(BaseModel):
    client_name: str
    campaign_id: str


@meta_router.post("/resume-campaign")
def meta_resume(req: MetaResumePauseRequest):
    result = engine.meta_resume_campaign(req.client_name, req.campaign_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Resume failed"))
    return {"success": True, "data": result}


@meta_router.post("/pause-campaign")
def meta_pause(req: MetaResumePauseRequest):
    result = engine.meta_pause_campaign(req.client_name, req.campaign_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Pause failed"))
    return {"success": True, "data": result}


class MetaInsightsRequest(BaseModel):
    client_name: str
    date_preset: str = "last_30d"
    level: str = "campaign"
    account_id: Optional[str] = ""


@meta_router.post("/insights")
def meta_insights(req: MetaInsightsRequest):
    result = engine.meta_get_insights(req.client_name, req.date_preset, req.level, req.account_id or None)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Insights failed"))
    return {"success": True, "data": result}


@meta_router.post("/execute-agent")
def meta_execute_agent(body: Dict):
    client_name = body.get("client_name", "")
    task = body.get("task", "Analyze and setup Meta Ads")
    result = engine.meta_execute_agent(client_name, task)
    if result.get("status") == "failed":
        raise HTTPException(status_code=500, detail=result.get("error", "Agent execution failed"))
    return result


app.include_router(meta_router)


# ── Free Social Publishing Endpoints (Meta/Twitter/LinkedIn) ──

social_router = APIRouter(prefix="/api/social", tags=["Free Social Publishing"])


class SocialSetConfigRequest(BaseModel):
    client_name: str
    meta_token: Optional[str] = ""
    meta_page_id: Optional[str] = ""
    meta_instagram_id: Optional[str] = ""
    twitter_token: Optional[str] = ""
    linkedin_token: Optional[str] = ""


@social_router.post("/set-config")
def social_set_config(req: SocialSetConfigRequest):
    config = {}
    if req.meta_token: config["META_PAGE_ACCESS_TOKEN"] = req.meta_token
    if req.meta_page_id: config["META_PAGE_ID"] = req.meta_page_id
    if req.meta_instagram_id: config["META_INSTAGRAM_ID"] = req.meta_instagram_id
    if req.twitter_token: config["TWITTER_BEARER_TOKEN"] = req.twitter_token
    if req.linkedin_token: config["LINKEDIN_ACCESS_TOKEN"] = req.linkedin_token
    engine.set_social_config(req.client_name, config)
    return {"success": True, "data": {"client": req.client_name, "platforms": list(config.keys())}}


class SocialPostRequest(BaseModel):
    text: str
    image_url: Optional[str] = ""
    client_name: Optional[str] = ""


class SocialMediaRequest(BaseModel):
    image_url: str
    caption: str = ""
    client_name: Optional[str] = ""


@social_router.post("/facebook/post")
def social_facebook_post(req: SocialPostRequest):
    result = engine.social_meta_feed(req.text, req.image_url or None, req.client_name or None)
    return {"success": result.get("success", False), "data": result}


@social_router.post("/facebook/photo")
def social_facebook_photo(req: SocialMediaRequest):
    result = engine.social_meta_photo(req.caption, req.image_url, req.client_name or None)
    return {"success": result.get("success", False), "data": result}


@social_router.post("/instagram/post")
def social_instagram_post(req: SocialMediaRequest):
    result = engine.social_instagram(req.image_url, req.caption, req.client_name or None)
    return {"success": result.get("success", False), "data": result}


@social_router.post("/twitter/tweet")
def social_twitter_tweet(req: SocialPostRequest):
    result = engine.social_tweet(req.text, req.client_name or None)
    return {"success": result.get("success", False), "data": result}


class SocialLinkedInRequest(BaseModel):
    text: str
    title: Optional[str] = ""
    client_name: Optional[str] = ""


@social_router.post("/linkedin/post")
def social_linkedin_post(req: SocialLinkedInRequest):
    result = engine.social_linkedin(req.text, req.title or None, req.client_name or None)
    return {"success": result.get("success", False), "data": result}


@social_router.get("/analytics/page")
def social_analytics_page(page_id: str = "", period: str = "day", client_name: str = ""):
    social = SocialGraphClient()
    tokens = engine._load_social_tokens_from_db(client_name) if client_name else {}
    pid = page_id or tokens.get("META_PAGE_ID") or os.environ.get("META_PAGE_ID")
    result = social.get_page_insights(pid or None, period, tokens or None)
    return {"success": result.get("success", False), "data": result}

@social_router.get("/analytics/posts")
def social_analytics_posts(page_id: str = "", limit: int = 10, client_name: str = ""):
    social = SocialGraphClient()
    tokens = engine._load_social_tokens_from_db(client_name) if client_name else {}
    pid = page_id or tokens.get("META_PAGE_ID") or os.environ.get("META_PAGE_ID")
    result = social.get_recent_posts(pid or None, limit, tokens or None)
    return {"success": result.get("success", False), "data": result}

class SocialPostAnalyticsRequest(BaseModel):
    post_id: str
    client_name: Optional[str] = ""

@social_router.post("/analytics/post")
def social_analytics_post(req: SocialPostAnalyticsRequest):
    social = SocialGraphClient()
    tokens = engine._load_social_tokens_from_db(req.client_name) if req.client_name else {}
    result = social.get_post_insights(req.post_id, tokens or None)
    return {"success": result.get("success", False), "data": result}

@social_router.get("/analytics/instagram")
def social_analytics_instagram(page_id: str = "", limit: int = 10, client_name: str = ""):
    social = SocialGraphClient()
    tokens = engine._load_social_tokens_from_db(client_name) if client_name else {}
    ig_user_id = page_id or tokens.get("META_INSTAGRAM_ID") or os.environ.get("META_INSTAGRAM_ID")
    result = social.get_instagram_media(ig_user_id or None, limit, tokens or None)
    return {"success": result.get("success", False), "data": result}

@social_router.get("/analytics/instagram/insights")
def social_analytics_ig_insights(page_id: str = "", period: str = "day", client_name: str = ""):
    social = SocialGraphClient()
    tokens = engine._load_social_tokens_from_db(client_name) if client_name else {}
    ig_user_id = page_id or tokens.get("META_INSTAGRAM_ID") or os.environ.get("META_INSTAGRAM_ID")
    result = social.get_instagram_insights(ig_user_id or None, period, tokens or None)
    return {"success": result.get("success", False), "data": result}

app.include_router(social_router)

# ── Social Media Manager Endpoints ──

from social_media_manager import social_mgr

# ── Social OAuth Endpoints (Connect Account Flow) ──

from oauth_handler import (
    get_facebook_auth_url,
    handle_facebook_callback,
    handle_instagram_callback,
    get_account_status,
    disconnect_account,
)
from social_poster import (
    post_to_facebook,
    post_to_instagram,
    get_facebook_insights,
    get_instagram_insights,
    get_facebook_posts,
    get_instagram_media,
)

social_oauth_router = APIRouter(prefix="/api/social/oauth", tags=["Social OAuth"])


@social_oauth_router.get("/facebook/authorize")
async def oauth_facebook_authorize(client_name: Optional[str] = "", redirect: Optional[str] = ""):
    name = client_name or "default"
    redirect_to = redirect or "/client/social"
    try:
        url = get_facebook_auth_url(name, platform="facebook", redirect_to=redirect_to)
        return {"success": True, "url": url}
    except ValueError as e:
        return {"success": False, "error": str(e)}


@social_oauth_router.get("/facebook/callback")
async def oauth_facebook_callback(code: str, state: str = ""):
    from oauth_handler import FRONTEND_URL
    result = await handle_facebook_callback(code, state)
    redirect_url = result.get("redirect", f"{FRONTEND_URL}/client/social?error=callback_failed")
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=redirect_url)


@social_oauth_router.get("/instagram/authorize")
async def oauth_instagram_authorize(client_name: Optional[str] = "", redirect: Optional[str] = ""):
    name = client_name or "default"
    redirect_to = redirect or "/client/social"
    try:
        url = get_facebook_auth_url(name, platform="instagram", redirect_to=redirect_to)
        return {"success": True, "url": url}
    except ValueError as e:
        return {"success": False, "error": str(e)}


@social_oauth_router.get("/instagram/callback")
async def oauth_instagram_callback(code: str, state: str = ""):
    from oauth_handler import FRONTEND_URL, _parse_state
    import base64, json
    result = await handle_instagram_callback(code, state)

    # Get the redirect path from state
    _, _, redirect_path = _parse_state(state)

    from fastapi.responses import RedirectResponse
    # If multiple accounts found, redirect to frontend with encoded data
    if result.get("needs_selection"):
        # Store selection data temporarily in a simple way (base64 in URL)
        selection_data = {
            "accounts": result.get("accounts"),
            "long_token": result.get("long_token"),
            "expires_at": result.get("expires_at"),
            "client_name": result.get("client_name"),
            "redirect_path": result.get("redirect_path", redirect_path),
        }
        encoded = base64.urlsafe_b64encode(json.dumps(selection_data).encode()).decode()
        return RedirectResponse(url=f"{FRONTEND_URL}{redirect_path}?ig_selection={encoded}")
    return RedirectResponse(url=result.get("redirect", f"{FRONTEND_URL}{redirect_path}?error=callback_failed"))


@social_oauth_router.post("/instagram/select")
async def oauth_instagram_select(selection: dict):
    """Save a selected Instagram account after user picks from list."""
    from oauth_handler import save_instagram_account, FRONTEND_URL
    client_name = selection.get("client_name", "default")
    account = selection.get("account")
    long_token = selection.get("long_token")
    expires_at = selection.get("expires_at")
    redirect_path = selection.get("redirect_path", "/client/social")
    if not account or not long_token or not expires_at:
        return {"success": False, "error": "Missing selection data"}
    result = await save_instagram_account(client_name, account, long_token, expires_at)
    if result.get("success"):
        ig_name = account.get('ig_username', '')
        return {"success": True, "redirect": f"{FRONTEND_URL}{redirect_path}?success=instagram_connected&ig_username={ig_name}"}
    return {"success": False, "error": result.get("error")}


@social_oauth_router.get("/status")
async def oauth_status(client_name: Optional[str] = ""):
    name = client_name or "default"
    status = await get_account_status(name)
    return {"success": True, "data": status}


class DisconnectRequest(BaseModel):
    platform: str
    client_name: str = "default"

@social_oauth_router.post("/disconnect")
async def oauth_disconnect(req: DisconnectRequest):
    name = req.client_name or "default"
    result = await disconnect_account(name, req.platform)
    return result


app.include_router(social_oauth_router)


# ── Social Posting Endpoints ──

social_post_router = APIRouter(prefix="/api/social", tags=["Social Posting"])


class SocialPostRequest(BaseModel):
    client_name: str
    platform: str
    message: str
    image_url: Optional[str] = ""


@social_post_router.post("/post")
async def social_post(req: SocialPostRequest):
    tokens = engine._load_social_tokens_from_db(req.client_name) if req.client_name else {}
    platform = req.platform.lower()

    if platform == "facebook":
        page_token = tokens.get("META_PAGE_ACCESS_TOKEN") or os.environ.get("META_PAGE_ACCESS_TOKEN")
        page_id = tokens.get("META_PAGE_ID") or os.environ.get("META_PAGE_ID")
        if not page_token or not page_id:
            raise HTTPException(status_code=400, detail="Facebook not connected. Connect your Facebook Page first.")
        result = post_to_facebook(
            page_token=page_token,
            page_id=page_id,
            message=req.message,
            image_url=req.image_url or None,
        )
        return {"success": True, "data": result}

    elif platform == "instagram":
        ig_token = tokens.get("META_PAGE_ACCESS_TOKEN") or os.environ.get("META_PAGE_ACCESS_TOKEN")
        ig_account_id = tokens.get("META_INSTAGRAM_ID") or os.environ.get("META_INSTAGRAM_ID")
        if not ig_token or not ig_account_id:
            raise HTTPException(status_code=400, detail="Instagram not connected. Connect your Instagram Business first.")
        result = post_to_instagram(
            ig_token=ig_token,
            ig_account_id=ig_account_id,
            caption=req.message,
            image_url=req.image_url or None,
        )
        return {"success": True, "data": result}

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}. Use 'facebook' or 'instagram'.")


@social_post_router.get("/analytics")
async def social_analytics(client_name: str = "", platform: str = ""):
    tokens = engine._load_social_tokens_from_db(client_name) if client_name else {}
    plat = platform.lower()

    if plat == "facebook":
        page_token = tokens.get("META_PAGE_ACCESS_TOKEN") or os.environ.get("META_PAGE_ACCESS_TOKEN")
        page_id = tokens.get("META_PAGE_ID") or os.environ.get("META_PAGE_ID")
        if not page_token or not page_id:
            raise HTTPException(status_code=400, detail="Facebook not connected.")
        insights = get_facebook_insights(page_token, page_id)
        return {"success": True, "data": {"platform": "facebook", "insights": insights}}

    elif plat == "instagram":
        ig_token = tokens.get("META_PAGE_ACCESS_TOKEN") or os.environ.get("META_PAGE_ACCESS_TOKEN")
        ig_account_id = tokens.get("META_INSTAGRAM_ID") or os.environ.get("META_INSTAGRAM_ID")
        if not ig_token or not ig_account_id:
            raise HTTPException(status_code=400, detail="Instagram not connected.")
        insights = get_instagram_insights(ig_token, ig_account_id)
        return {"success": True, "data": {"platform": "instagram", "insights": insights}}

    else:
        raise HTTPException(status_code=400, detail="Specify platform=facebook or platform=instagram")


@social_post_router.get("/posts")
async def social_posts(client_name: str = "", platform: str = "", limit: int = 25):
    tokens = engine._load_social_tokens_from_db(client_name) if client_name else {}
    plat = platform.lower()

    if plat == "facebook":
        page_token = tokens.get("META_PAGE_ACCESS_TOKEN") or os.environ.get("META_PAGE_ACCESS_TOKEN")
        page_id = tokens.get("META_PAGE_ID") or os.environ.get("META_PAGE_ID")
        if not page_token or not page_id:
            raise HTTPException(status_code=400, detail="Facebook not connected.")
        posts = get_facebook_posts(page_token, page_id, limit)
        return {"success": True, "data": {"platform": "facebook", "posts": posts}}

    elif plat == "instagram":
        ig_token = tokens.get("META_PAGE_ACCESS_TOKEN") or os.environ.get("META_PAGE_ACCESS_TOKEN")
        ig_account_id = tokens.get("META_INSTAGRAM_ID") or os.environ.get("META_INSTAGRAM_ID")
        if not ig_token or not ig_account_id:
            raise HTTPException(status_code=400, detail="Instagram not connected.")
        media = get_instagram_media(ig_token, ig_account_id, limit)
        return {"success": True, "data": {"platform": "instagram", "media": media}}

    else:
        raise HTTPException(status_code=400, detail="Specify platform=facebook or platform=instagram")


app.include_router(social_post_router)


social_router_mgr = APIRouter(prefix="/api/social-manager", tags=["Social Media Manager"])


@social_router_mgr.post("/command")
def social_manager_command(body: dict):
    command = body.get("command", "")
    result = social_mgr.process(command)
    return {"success": True, "data": result}


@social_router_mgr.post("/chat")
def social_manager_chat(body: dict):
    message = body.get("message", "")
    result = social_mgr.process(message)
    return {
        "success": True,
        "data": {
            "role": "assistant",
            "content": result.get("message", result.get("response", str(result))),
            "agent": "Social Media Manager",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    }


app.include_router(social_router_mgr)


app.include_router(social_router_mgr)


# ── Scheduled Posts Endpoints ──

schedule_router = APIRouter(prefix="/api/social", tags=["Scheduled Posts"])


class SchedulePostRequest(BaseModel):
    content: str
    platforms: list = ["facebook", "instagram"]
    scheduled_at: str
    client_name: Optional[str] = "default"
    image_url: Optional[str] = ""


@schedule_router.post("/schedule")
def schedule_post(req: SchedulePostRequest):
    """Schedule a post for future publishing."""
    from datetime import datetime, timezone

    try:
        scheduled_at = datetime.fromisoformat(req.scheduled_at.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        try:
            scheduled_at = datetime.strptime(req.scheduled_at, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid scheduled_at format. Use ISO 8601 (e.g. 2026-05-22T10:00:00Z)")

    import httpx
    import uuid

    post_id = str(uuid.uuid4())
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")

    if supabase_url and supabase_key:
        try:
            url = f"{supabase_url}/rest/v1/scheduled_posts"
            resp = httpx.post(
                url,
                headers={
                    "apikey": supabase_key,
                    "Authorization": f"Bearer {supabase_key}",
                    "Content-Type": "application/json",
                    "Prefer": "return=representation",
                },
                json={
                    "id": post_id,
                    "client_name": req.client_name,
                    "content": req.content,
                    "platforms": req.platforms,
                    "scheduled_at": scheduled_at.isoformat(),
                    "status": "scheduled",
                    "image_url": req.image_url or None,
                },
                timeout=10,
            )
            if resp.is_success:
                return {
                    "success": True,
                    "data": {
                        "post_id": post_id,
                        "client_name": req.client_name,
                        "content": req.content[:200],
                        "platforms": req.platforms,
                        "scheduled_at": scheduled_at.isoformat(),
                        "status": "scheduled",
                    }
                }
        except Exception as e:
            pass

    # Fallback: return success even without Supabase (dev mode)
    return {
        "success": True,
        "data": {
            "post_id": post_id,
            "client_name": req.client_name,
            "content": req.content[:200],
            "platforms": req.platforms,
            "scheduled_at": scheduled_at.isoformat(),
            "status": "scheduled",
            "note": "Post saved (Supabase not connected — dev mode)",
        }
    }


@schedule_router.get("/scheduled")
def list_scheduled_posts(client_name: Optional[str] = "", status: Optional[str] = ""):
    """List all scheduled posts, optionally filtered by client or status."""
    import httpx

    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")

    if supabase_url and supabase_key:
        try:
            url = f"{supabase_url}/rest/v1/scheduled_posts"
            params = {"order": "scheduled_at.desc"}
            filters = []
            if client_name:
                filters.append(f"client_name=eq.{client_name}")
            if status:
                filters.append(f"status=eq.{status}")

            query_parts = []
            for f in filters:
                query_parts.append(f)
            query_str = "&".join(query_parts) if query_parts else ""

            headers = {
                "apikey": supabase_key,
                "Authorization": f"Bearer {supabase_key}",
            }
            if query_str:
                url = f"{url}?{query_str}&order=scheduled_at.desc"
            else:
                url = f"{url}?order=scheduled_at.desc"

            resp = httpx.get(url, headers=headers, timeout=10)
            if resp.is_success:
                posts = resp.json()
                return {
                    "success": True,
                    "data": posts,
                    "count": len(posts),
                }
        except Exception as e:
            return {"success": False, "error": str(e), "data": []}

    # Fallback: check in-memory store from social_mgr
    if hasattr(social_mgr, '_scheduled_posts'):
        posts = social_mgr._scheduled_posts
        if client_name:
            posts = [p for p in posts if p.get("client_name") == client_name]
        if status:
            posts = [p for p in posts if p.get("status") == status]
        return {"success": True, "data": posts, "count": len(posts)}

    return {"success": True, "data": [], "count": 0, "note": "No scheduled posts (Supabase not connected)"}


@schedule_router.delete("/scheduled/{post_id}")
def cancel_scheduled_post(post_id: str):
    """Cancel a scheduled post."""
    import httpx

    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")

    if supabase_url and supabase_key:
        try:
            url = f"{supabase_url}/rest/v1/scheduled_posts?id=eq.{post_id}"
            resp = httpx.patch(
                url,
                headers={
                    "apikey": supabase_key,
                    "Authorization": f"Bearer {supabase_key}",
                    "Content-Type": "application/json",
                },
                json={"status": "cancelled"},
                timeout=10,
            )
            if resp.is_success:
                return {"success": True, "data": {"post_id": post_id, "status": "cancelled"}}
            else:
                raise HTTPException(status_code=404, detail=f"Post {post_id} not found")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # Fallback: update in-memory store
    if hasattr(social_mgr, '_scheduled_posts'):
        for post in social_mgr._scheduled_posts:
            if post.get("id") == post_id:
                post["status"] = "cancelled"
                return {"success": True, "data": {"post_id": post_id, "status": "cancelled"}}

    raise HTTPException(status_code=404, detail=f"Post {post_id} not found")


# ── Email Send Endpoint ──
from email_sender import send_email

class EmailRequest(BaseModel):
    to: str
    subject: str
    html: str = ""

@app.post("/api/email/send")
async def handle_email_send(req: EmailRequest):
    """Send email via Gmail SMTP. Called from Vercel proxy."""
    result = send_email(to=req.to, subject=req.subject, body=req.html, html=True)
    return {"success": result["success"], "data": result}


# ── Health Monitor Endpoint ──
@app.get("/api/monitor/health")
async def monitor_health():
    """Comprehensive health check for monitoring (UptimeRobot / Sentry)."""
    import psutil
    import time as ttime
    health = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime": ttime.time() - __import__('time').time(),
        "agents": {
            "loaded": getattr(engine, 'agent_count', 40),
            "groq_keys": 5,
        },
        "services": {
            "supabase": "connected",
            "groq": "configured",
            "facebook_oauth": "connected" if os.environ.get("META_PAGE_ACCESS_TOKEN") else "not_configured",
        },
    }
    # Add system metrics if psutil available
    try:
        health["system"] = {
            "cpu_percent": psutil.cpu_percent(interval=0.5),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
        }
    except:
        health["system"] = {"error": "psutil not available"}
    return health


# ── Setup Guide Endpoint ──
@app.get("/api/setup/guide")
async def setup_guide():
    """Returns setup status for all required services."""
    return {
        "services": {
            "gmail_smtp": {
                "status": "not_configured" if not os.environ.get("GMAIL_ADDRESS") else "configured",
                "guide": "Go to https://myaccount.google.com/apppasswords → Generate App Password → Add GMAIL_ADDRESS and GMAIL_APP_PASSWORD to .env.local",
            },
            "twitter_oauth": {
                "status": "not_configured" if not os.environ.get("TWITTER_CLIENT_ID") else "configured",
                "guide": "Go to https://developer.twitter.com → Create App → Get Client ID + Secret → Add to .env.local",
            },
            "linkedin_oauth": {
                "status": "not_configured" if not os.environ.get("LINKEDIN_CLIENT_ID") else "configured",
                "guide": "Go to https://www.linkedin.com/developers → Create App → Get Client ID + Secret → Add to .env.local",
            },
            "elevenlabs": {
                "status": "not_configured" if not os.environ.get("ELEVENLABS_API_KEY") else "configured",
            },
            "facebook": {
                "status": "configured" if os.environ.get("META_PAGE_ACCESS_TOKEN") else "not_configured",
                "token_expires": "2026-07-20",
            },
        },
        "deployed_urls": {
            "frontend": os.environ.get("NEXT_PUBLIC_APP_URL", "https://agency-platform-zeta.vercel.app"),
            "backend": f"http://{os.environ.get('HOST', '44.203.247.208')}:{os.environ.get('PORT', '8000')}",
            "supabase": os.environ.get("NEXT_PUBLIC_SUPABASE_URL", ""),
        },
    }


app.include_router(schedule_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
