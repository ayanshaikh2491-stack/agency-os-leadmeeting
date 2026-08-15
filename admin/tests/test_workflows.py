"""Tests for the real workflow execution endpoints.

Run: pytest admin/tests/test_workflows.py
"""
import asyncio
import sys

sys.path.insert(0, r"C:\Users\TAUSHEF\Downloads\int")

from admin.api.routes import workflows as wf


def _run(coro):
    return asyncio.run(coro)


def test_list_workflows_returns_all_eight():
    out = _run(wf.list_workflows())
    assert out["success"] is True
    ids = {w["id"] for w in out["data"]}
    assert len(ids) == 8
    assert "seo-optimize" in ids
    assert "speed-to-lead" in ids


def test_unknown_workflow_rejected():
    out = _run(wf.run_workflow("does-not-exist"))
    assert out["success"] is False
    assert "known" in out


def test_quality_review_runs_and_completes():
    # quality-review uses list_pending_reviews (no LLM) -> safe + fast.
    out = _run(wf.run_workflow("quality-review"))
    assert out["success"] is True
    assert out["status"] == "queued"
    run_id = out["run_id"]

    async def wait():
        for _ in range(50):
            rec = wf._run_history[run_id]
            if rec["status"] in ("completed", "failed"):
                return rec
            await asyncio.sleep(0.1)
        return wf._run_history[run_id]

    rec = _run(wait())
    assert rec["status"] == "completed", rec
    assert "pending_reviews" in rec["result"]


def test_status_endpoint_polls_latest_run():
    out = _run(wf.run_workflow("nurture-pipeline"))
    run_id = out["run_id"]

    async def wait():
        for _ in range(50):
            if wf._run_history[run_id]["status"] in ("completed", "failed"):
                break
            await asyncio.sleep(0.1)

    _run(wait())
    status = _run(wf.workflow_status("nurture-pipeline"))
    assert status["success"] is True
    assert status["run"]["run_id"] == run_id
    assert status["run"]["status"] == "completed"
