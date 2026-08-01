"""TAGS Agency OS — FastAPI backend entry point."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from admin.api.models.schemas import HealthResponse
from admin.api.routes import ceo as ceo_routes
from admin.api.routes import sba as sba_routes
from admin.api.routes import swarm as swarm_routes
from admin.api.routes import workspace as workspace_routes
from admin.api.routes import communication as comm_routes
from admin.api.routes import seo as seo_routes
from admin.api.routes import content as content_routes
from admin.api.routes import kaggle as kaggle_routes
from admin.api.routes import orchestrator as orch_routes
from admin.api.routes import ads as ads_routes
from admin.api.routes import analytics as analytics_routes
from admin.api.routes import social as social_routes
from admin.config import settings
from admin.database import close_db, init_db
from admin.agency.sba_store import load_all_from_db
from admin.workspace.manager import list_workspaces

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    await init_db()
    await load_all_from_db()
    yield
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
app.include_router(swarm_routes.router)
app.include_router(workspace_routes.router)
app.include_router(comm_routes.router)
app.include_router(seo_routes.router)
app.include_router(content_routes.router)
app.include_router(kaggle_routes.router)
app.include_router(orch_routes.router)
app.include_router(ads_routes.router)
app.include_router(analytics_routes.router)
app.include_router(social_routes.router)


# ── Health ─────────────────────────────────────────────────────────────────


@app.get("/api/health", response_model=HealthResponse, tags=["system"])
async def health():
    workspaces = list_workspaces()
    return HealthResponse(
        ceo_ready=True,
        workspace_count=len(workspaces),
    )


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
