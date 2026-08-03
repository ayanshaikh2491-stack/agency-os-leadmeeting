"""Workflows API Routes — agency workflow definitions + triggers.

Endpoints:
  GET  /api/workflows              — List workflow definitions
  POST /api/workflows/{id}/run     — Trigger a workflow run
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/workflows", tags=["workflows"])

# Static workflow registry — mirrors the frontend Workflows page
WORKFLOWS: list[dict[str, Any]] = [
    {"id": "speed-to-lead", "name": "Speed to Lead", "description": "Instant lead response via SMS + email + LinkedIn"},
    {"id": "intake-research", "name": "Intake Research", "description": "Client intake -> VOC analysis -> ICP -> positioning"},
    {"id": "content-pipeline", "name": "Content Pipeline", "description": "Blog -> social -> ad copy -> email sequence"},
    {"id": "nurture-pipeline", "name": "Nurture Pipeline", "description": "Lead nurturing: emails, retargeting, follow-ups"},
    {"id": "seo-optimize", "name": "SEO Optimization", "description": "Keyword research -> on-page -> content optimization"},
    {"id": "analytics-report", "name": "Analytics Report", "description": "Weekly/Monthly analytics & performance reports"},
    {"id": "client-onboard", "name": "Client Onboarding", "description": "Welcome sequence -> kickoff call -> setup"},
    {"id": "quality-review", "name": "Quality Review", "description": "Content QC, compliance check, brand alignment"},
]


@router.get("")
async def list_workflows() -> dict[str, Any]:
    """List all workflow definitions."""
    return {"success": True, "data": WORKFLOWS}


@router.post("/{workflow_id}/run")
async def run_workflow(workflow_id: str) -> dict[str, Any]:
    """Trigger a workflow. Execution is async; returns an accepted ack.

    TODO: wire to real agent orchestration (orchestrator / SBA tools).
    """
    known = [w["id"] for w in WORKFLOWS]
    if workflow_id not in known:
        return {"success": False, "error": f"Unknown workflow '{workflow_id}'", "known": known}

    return {
        "success": True,
        "id": workflow_id,
        "status": "started",
        "message": f"Workflow '{workflow_id}' triggered",
    }
