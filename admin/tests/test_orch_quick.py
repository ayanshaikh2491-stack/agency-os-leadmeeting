"""Orchestrator quick smoke tests — workspace CRUD, report chain, scheduler, planner."""
import sys
from datetime import datetime, timezone

sys.path.insert(0, ".")


def test_orchestrator_imports():
    from admin.agency.orchestrator import (  # noqa: F401
        create_workspace, list_workspaces, get_workspace, delete_workspace,
        register_agent, submit_report, get_pending_reports,
        run_seo_agent_for_workspace, setup_agency, setup_client_workspace,
    )
    from admin.agency.scheduler import (  # noqa: F401
        create_schedule, get_schedules, run_due_tasks, get_due_tasks,
        setup_default_schedules,
    )
    from admin.api.routes.orchestrator import router  # noqa: F401


def test_workspace_crud():
    from admin.agency.orchestrator import (
        create_workspace, delete_workspace, get_workspace, list_workspaces,
    )

    ws = create_workspace("SmokeClient", "John Doe", "client", {"target_url": "https://example.com"})
    try:
        assert ws["name"] == "SmokeClient"
        assert ws["id"]
        assert any(w["id"] == ws["id"] for w in list_workspaces())
        got = get_workspace(ws["id"])
        assert got["id"] == ws["id"]
    finally:
        delete_workspace(ws["id"])


def test_report_chain():
    from admin.agency.orchestrator import (
        get_pending_reports, setup_agency, setup_client_workspace, submit_report,
    )

    agency = setup_agency()
    client = setup_client_workspace("SmokeDemo", "https://example.com", ["seo tips", "marketing"])
    try:
        report = submit_report(
            client["id"], "seo", "seo", "agency",
            "onpage_check",
            {"url": "https://example.com", "seo_score": 75},
            summary="Demo report for testing",
        )
        assert report["id"]
        pending = get_pending_reports("seo")
        assert isinstance(pending, list)
    finally:
        from admin.agency.orchestrator import delete_workspace
        delete_workspace(client["id"])
        delete_workspace(agency["id"])


def test_planner_creates_plan():
    from admin.agency.planner import create_seo_plan

    plan = create_seo_plan("smoke_ws", "https://example.com", ["seo", "marketing"])
    assert "tasks" in plan
    assert len(plan["tasks"]) > 0


def test_scheduler_due_tasks():
    from admin.agency.orchestrator import delete_workspace
    from admin.agency.scheduler import (
        _schedules, create_schedule, get_due_tasks, get_schedules,
    )

    sched = create_schedule("smoke_ws", "onpage_check", {"url": "https://x.com"}, "daily")
    assert sched["frequency"] == "daily"
    # Force due so get_due_tasks sees it
    for s in get_schedules():
        _schedules[s["id"]]["next_run"] = "2020-01-01T00:00:00+00:00"
    due = get_due_tasks()
    assert isinstance(due, list)
