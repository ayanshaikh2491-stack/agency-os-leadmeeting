"""FastAPI endpoints for swarm coordination."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from admin.agency.swarm import swarm

router = APIRouter(prefix="/api/swarm", tags=["swarm"])


class AddAgentRequest(BaseModel):
    agent_id: str
    role: str  # coordinator, worker, observer


class AssignTaskRequest(BaseModel):
    agent_id: str
    task: str


@router.post("/agents/add")
async def add_agent(req: AddAgentRequest):
    """Add agent to swarm."""
    await swarm.add_agent(req.agent_id, req.role)
    return {"status": "added", "agent_id": req.agent_id}


@router.post("/tasks/assign")
async def assign_task(req: AssignTaskRequest):
    """Assign task to agent."""
    try:
        await swarm.assign_task(req.agent_id, req.task)
        return {"status": "assigned", "agent_id": req.agent_id, "task": req.task}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/run")
async def run_swarm():
    """Run swarm workflow."""
    await swarm.run()
    return {"status": "running"}