"""Orchestrator, planner, scheduler, and API routes tests (proper pytest)."""
import sys

sys.path.insert(0, ".")


def test_orch_imports():
    from admin.agency.orchestrator import (  # noqa: F401
        create_workspace, list_workspaces, get_workspace, delete_workspace,
        register_agent, submit_report, get_pending_reports,
        run_seo_agent_for_workspace, setup_agency, setup_client_workspace,
    )


def test_planner_imports():
    from admin.agency.planner import (  # noqa: F401
        create_seo_plan, execute_plan, execute_plan_and_report, get_plans,
    )


def test_scheduler_imports():
    from admin.agency.scheduler import (  # noqa: F401
        create_schedule, get_schedules, run_due_tasks, get_due_tasks,
        setup_default_schedules, setup_agency_schedules,
    )


def test_api_routes_registered():
    from admin.api.routes.orchestrator import router

    paths = [r.path for r in router.routes if hasattr(r, "path")]
    assert len(paths) >= 15


def test_create_workspace():
    from admin.agency.orchestrator import create_workspace, delete_workspace

    ws = create_workspace("Test Client", "John Doe", "client", {"target_url": "https://example.com"})
    try:
        assert ws["name"] == "Test Client"
        assert ws["client_name"] == "John Doe"
        assert ws["type"] == "client"
    finally:
        delete_workspace(ws["id"])


def test_list_workspaces():
    from admin.agency.orchestrator import create_workspace, delete_workspace, list_workspaces

    ws1 = create_workspace("WS1", "C1")
    ws2 = create_workspace("WS2", "C2")
    try:
        ids = {w["id"] for w in list_workspaces()}
        assert ws1["id"] in ids and ws2["id"] in ids
    finally:
        delete_workspace(ws1["id"])
        delete_workspace(ws2["id"])


def test_report_flow_light():
    """Client SEO -> report submitted -> pending reports visible (no live agent run)."""
    from admin.agency.orchestrator import (
        delete_workspace, get_pending_reports, setup_agency,
        setup_client_workspace, submit_report,
    )

    agency = setup_agency()
    client = setup_client_workspace("TestClient", "https://example.com", ["test keyword"])
    try:
        report = submit_report(
            client["id"], "seo", "seo", "agency",
            "onpage_check",
            {"url": "https://example.com", "seo_score": 75},
            summary="smoke report",
        )
        assert report["id"]
        pending = get_pending_reports("seo")
        assert any(r["id"] == report["id"] for r in pending)
    finally:
        delete_workspace(client["id"])
        delete_workspace(agency["id"])


def test_plan_creation_with_tasks():
    from admin.agency.planner import create_seo_plan

    plan = create_seo_plan("ws_test", "https://example.com", ["seo", "marketing"])
    assert plan["workspace_id"] == "ws_test"
    assert len(plan["tasks"]) >= 7
    task_types = [t["type"] for t in plan["tasks"]]
    assert "site_audit" in task_types
    assert "onpage_check" in task_types
    assert "track_rankings" in task_types
    assert "generate_report" in task_types


def test_schedule_crud():
    from admin.agency.scheduler import create_schedule, delete_schedule, get_schedules

    s = create_schedule("ws_test", "onpage_check", {"url": "https://x.com"}, "daily")
    try:
        assert s["workspace_id"] == "ws_test"
        assert s["frequency"] == "daily"
        assert any(x["id"] == s["id"] for x in get_schedules("ws_test"))
    finally:
        delete_schedule(s["id"])


def test_due_tasks_detection():
    from admin.agency.scheduler import (
        _schedules, create_schedule, delete_schedule, get_due_tasks,
    )

    s = create_schedule("ws_test2", "onpage_check", {"url": "https://x.com"}, "daily")
    try:
        _schedules[s["id"]]["next_run"] = "2020-01-01T00:00:00+00:00"
        due = get_due_tasks()
        assert any(t["id"] == s["id"] for t in due)
    finally:
        delete_schedule(s["id"])
