"""TAGS Agency OS — FastAPI backend entry point."""

from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from admin.api.models.schemas import HealthResponse
from admin.api.routes import ceo as ceo_routes
from admin.api.routes import sba as sba_routes
from admin.api.routes import workspace as workspace_routes
from admin.api.routes import communication as comm_routes
from admin.api.routes import seo as seo_routes
from admin.api.routes import content as content_routes
from admin.api.routes import kaggle as kaggle_routes
from admin.api.routes import orchestrator as orch_routes
from admin.api.routes import ads as ads_routes
from admin.api.routes import analytics as analytics_routes
from admin.api.routes import social as social_routes
from admin.api.routes import workflows as workflows_routes
from admin.api.routes import website as website_routes
from admin.api.routes import analyzing as analyzing_routes
from admin.api.routes import extra as extra_routes
from admin.api.routes import store as store_routes
from admin.api.routes import agent_aliases as agent_aliases_routes
from admin.api.routes import agents_crud as agents_crud_routes
from admin.api.routes import multiagent as multiagent_routes
from admin.config import settings
from admin.database import close_db, init_db
from admin.agency.sba_store import load_all_from_db as load_sba_from_db
from admin.workspace.manager import (
    list_workspaces,
    load_all_from_db as load_workspaces_from_db,
    seed_workspace,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    from admin.persistence import close_persistence, init_persistence, set_persistent_mode
    set_persistent_mode(True)  # long-running loop owns the shared DB connection
    await init_persistence()   # create workspace SQLite tables first
    await init_db()
    await load_sba_from_db()
    await load_workspaces_from_db()

    # ── PocketBase = durable source of truth ────────────────────────────────
    # Pull workspaces + custom agents from external PB into the local cache
    # BEFORE seeding defaults, so owner data survives container restarts and
    # every agent/workspace picks up right where it left off. Best-effort:
    # when POCKETBASE_URL is unset or unreachable, pure-local behaviour stays.
    try:
        from admin.workspace.manager import seed_from_pocketbase
        from admin.agency.agent_registry import sync_from_pocketbase

        await seed_from_pocketbase()
        _pulled_agents = await sync_from_pocketbase()
        if _pulled_agents:
            logging.getLogger("admin.main").info(
                "PocketBase: %d custom agent(s) restored.", _pulled_agents)
    except Exception as exc:  # noqa: BLE001
        logging.getLogger("admin.main").warning(
            "PocketBase boot-seed skipped (non-fatal): %s", exc)

    # Bind pre-provisioned Supabase schemas (ws_<slug>) to workspaces so the
    # Website Agent writes into the right schema on this deployment.
    seed_workspace(
        "ws_agency",
        "Agency Workspace",
        client_name="TAGS Agency",
        description="Agency-level workspace, bound to Supabase schema ws_agency.",
    )
    seed_workspace(
        "ws_default",
        "Default Workspace",
        client_name="Default Client",
        description="Default workspace, bound to Supabase schema ws_default.",
    )

    # ── Lifecycle gate (CRITICAL, must always run) ──────────────────────────
    # Every agent starts STANDBY (no 24/7 loop). CEO wakes them on demand. CEO
    # itself is the 24/7 listener (HTTP), not a loop. This MUST NOT be inside a
    # try block that can be skipped by an unrelated import failure.
    from admin.agency import lifecycle as lc

    for slug in ("ceo", "sba", "seo", "social", "website"):
        lc.register(slug)

    # ── Mandate table (best-effort; self-guards on first use) ───────────────
    try:
        from admin.agency import mandates as mandates_mod

        await mandates_mod.init_mandates_table()
    except Exception as exc:  # noqa: BLE001
        logging.getLogger("admin.main").warning("mandates init failed: %s", exc)

    yield
    await close_persistence()
    await close_db()


app = FastAPI(
    title="TAGS Agency OS",
    description="Multi-tenant agent orchestration backend",
    version="0.1.0",
    lifespan=lifespan,
)

# ── CORS — allow the Next.js frontend ──────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mount routers ──────────────────────────────────────────────────────────
app.include_router(ceo_routes.router)
app.include_router(ceo_routes._old_router)  # Legacy /api/chat/agency endpoint
app.include_router(sba_routes.router)
app.include_router(workspace_routes.router)
app.include_router(comm_routes.router)
app.include_router(seo_routes.router)
app.include_router(content_routes.router)
app.include_router(kaggle_routes.router)
app.include_router(orch_routes.router)
app.include_router(ads_routes.router)
app.include_router(analytics_routes.router)
app.include_router(social_routes.router)
app.include_router(workflows_routes.router)
app.include_router(website_routes.router)
app.include_router(analyzing_routes.router)
app.include_router(extra_routes.router)          # /api/status, /api/workspaces, agent status
app.include_router(store_routes.router)          # /api/store/* — client storefront (Shopify-like)
app.include_router(agent_aliases_routes.router)  # /api/agents + /api/agents/{id}/chat
app.include_router(agent_aliases_routes._seo_router)  # /api/agents/seo-engine/*
app.include_router(agents_crud_routes.router)        # /api/agents/custom/*
app.include_router(multiagent_routes.router)         # /api/ceo/run + /api/ceo/run/custom (multi-agent)


# ── Health ─────────────────────────────────────────────────────────────────


@app.get("/api/health", response_model=HealthResponse, tags=["system"])
async def health():
    workspaces = list_workspaces()
    return HealthResponse(
        ceo_ready=True,
        workspace_count=len(workspaces),
    )


@app.get("/api/status", tags=["system"])
async def api_status():
    """Agency status — pipeline summary + workspace count.

    Shape matches what the frontend expects:
      status?.pipeline?.queue?.total / .new / .leads_found_today
    """
    from admin.agency.sba_store import list_leads

    all_leads = list_leads()
    by_status: dict[str, int] = {}
    for s in ["new", "contacted", "meeting", "proposal", "negotiation", "closed", "lost"]:
        by_status[s] = len([l for l in all_leads if l["status"] == s])

    new_count = by_status.get("new", 0)
    total_in_pipeline = sum(by_status.values())
    hot_leads = len([l for l in all_leads if l.get("score", 0) >= 80 and l["status"] != "closed"])

    return {
        "success": True,
        "pipeline": {
            "leads_found_today": new_count,
            "queue": {"total": total_in_pipeline, "new": new_count},
            "by_status": by_status,
            "hot_leads": hot_leads,
        },
        "workspaces": len(list_workspaces()),
    }


# ── Entry ──────────────────────────────────────────────────────────────────


def main() -> None:
    """Start the FastAPI server.

    Uses reload=False for EC2 production.
    Set ADMIN_RELOAD=true env var to enable hot-reload for local dev.
    """
    uvicorn.run(
        "admin.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=os.getenv("ADMIN_RELOAD", "").lower() in ("1", "true", "yes"),
    )


if __name__ == "__main__":
    main()
