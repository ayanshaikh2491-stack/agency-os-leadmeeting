"""Test orchestrator, planner, scheduler, and API routes."""
import sys
sys.path.insert(0, ".")

passed = 0
failed = 0

def test(name, fn):
    global passed, failed
    try:
        fn()
        print(f"  [PASS] {name}")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] {name}: {e}")
        failed += 1

# ── Test imports ──────────────────────────────────────────────────────────

print("=== ORCHESTRATOR ===")

def test_orch_imports():
    from admin.agency.orchestrator import (
        create_workspace, list_workspaces, get_workspace, delete_workspace,
        register_agent, submit_report, get_pending_reports,
        run_seo_agent_for_workspace, aggregate_client_reports, submit_sba_to_ceo,
        setup_agency, setup_client_workspace
    )
test("orchestrator imports", test_orch_imports)

def test_planner_imports():
    from admin.agency.planner import create_seo_plan, execute_plan, execute_plan_and_report, get_plans
test("planner imports", test_planner_imports)

def test_scheduler_imports():
    from admin.agency.scheduler import (
        create_schedule, get_schedules, run_due_tasks, get_due_tasks,
        setup_default_schedules, setup_agency_schedules
    )
test("scheduler imports", test_scheduler_imports)

def test_api_routes():
    from admin.api.routes.orchestrator import router
    paths = [r.path for r in router.routes if hasattr(r, "path")]
    assert len(paths) >= 15, f"Expected 15+ routes, got {len(paths)}"
test("API routes import (15+ endpoints)", test_api_routes)

# ── Test workspace CRUD ──────────────────────────────────────────────────

print("\n=== WORKSPACE CRUD ===")

def test_create_workspace():
    from admin.agency.orchestrator import create_workspace, delete_workspace
    ws = create_workspace("Test Client", "John Doe", "client", {"target_url": "https://example.com"})
    assert ws["name"] == "Test Client"
    assert ws["client_name"] == "John Doe"
    assert ws["workspace_type"] == "client"
    delete_workspace(ws["id"])
test("create workspace", test_create_workspace)

def test_list_workspaces():
    from admin.agency.orchestrator import create_workspace, list_workspaces, delete_workspace
    ws1 = create_workspace("WS1", "C1")
    ws2 = create_workspace("WS2", "C2")
    all_ws = list_workspaces()
    assert len(all_ws) >= 2
    delete_workspace(ws1["id"])
    delete_workspace(ws2["id"])
test("list workspaces", test_list_workspaces)

# ── Test reporting chain ─────────────────────────────────────────────────

print("\n=== REPORTING CHAIN ===")

def test_report_flow():
    from admin.agency.orchestrator import (
        setup_agency, setup_client_workspace,
        run_seo_agent_for_workspace, aggregate_client_reports, submit_sba_to_ceo,
        get_pending_reports, delete_workspace
    )
    agency = setup_agency()
    client = setup_client_workspace("TestClient", "https://example.com", ["test keyword"])

    # 1. Client SEO agent runs and reports to agency SEO
    result = run_seo_agent_for_workspace(client["id"])
    assert "error" not in result, f"Run failed: {result}"
    assert result["report"]["to_agent_type"] == "seo"
    print(f"    -> Client SEO reported to Agency SEO: score={result['report']['data']['seo_score']}")

    # 2. Agency SEO aggregates and reports to SBA
    agg = aggregate_client_reports()
    assert agg["report"]["to_agent_type"] == "sba"
    assert agg["report"]["from_agent_type"] == "seo"
    print(f"    -> Agency SEO aggregated {agg['total_reports']} reports -> SBA")

    # 3. SBA forwards to CEO
    sba = submit_sba_to_ceo()
    assert sba["report"]["to_agent_type"] == "ceo"
    assert sba["report"]["from_agent_type"] == "sba"
    print(f"    -> SBA forwarded briefing to CEO")

    # 4. Check pending reports
    seo_pending = get_pending_reports("seo")
    sba_pending = get_pending_reports("sba")
    ceo_pending = get_pending_reports("ceo")
    print(f"    -> Pending: SEO={len(seo_pending)}, SBA={len(sba_pending)}, CEO={len(ceo_pending)}")

    delete_workspace(agency["id"])
    delete_workspace(client["id"])

test("full report chain (client->agency->SBA->CEO)", test_report_flow)

# ── Test planner ─────────────────────────────────────────────────────────

print("\n=== PLANNER ===")

def test_plan_creation():
    from admin.agency.planner import create_seo_plan
    plan = create_seo_plan("ws_test", "https://example.com", ["seo", "marketing"])
    assert plan["workspace_id"] == "ws_test"
    assert len(plan["tasks"]) >= 7  # audit + onpage + keyword + rankings + meta + schema + report
    task_types = [t["type"] for t in plan["tasks"]]
    assert "site_audit" in task_types
    assert "onpage_check" in task_types
    assert "track_rankings" in task_types
    assert "generate_report" in task_types
test("plan creation with tasks", test_plan_creation)

# ── Test scheduler ───────────────────────────────────────────────────────

print("\n=== SCHEDULER ===")

def test_schedule_crud():
    from admin.agency.scheduler import create_schedule, get_schedules, delete_schedule
    s = create_schedule("ws_test", "onpage_check", {"url": "https://x.com"}, "daily")
    assert s["workspace_id"] == "ws_test"
    assert s["frequency"] == "daily"
    schedules = get_schedules("ws_test")
    assert len(schedules) >= 1
    delete_schedule(s["id"])
test("schedule CRUD", test_schedule_crud)

def test_due_tasks():
    from admin.agency.scheduler import create_schedule, get_due_tasks, delete_schedule
    # Create a schedule that's already due
    s = create_schedule("ws_test2", "onpage_check", {"url": "https://x.com"}, "daily")
    # Force next_run to past
    from admin.agency.scheduler import _schedules
    _schedules[s["id"]]["next_run"] = "2020-01-01T00:00:00+00:00"
    due = get_due_tasks()
    assert len(due) >= 1
    delete_schedule(s["id"])
test("detect due tasks", test_due_tasks)

# ── Test API routes are registered ───────────────────────────────────────

print("\n=== API ROUTES ===")

def test_api_count():
    from admin.api.routes.orchestrator import router
    paths = [r.path for r in router.routes if hasattr(r, "path")]
    assert len(paths) >= 16, f"Expected 16+ routes, got {len(paths)}"
    print(f"    -> {len(paths)} routes registered")
    for p in sorted(paths):
        print(f"       {p}")
test("16+ orchestrator routes", test_api_count)

# ── Summary ──────────────────────────────────────────────────────────────

print(f"\n{'='*50}")
print(f"RESULTS: {passed} passed, {failed} failed")
if failed == 0:
    print("ALL TESTS PASSED!")
print(f"{'='*50}")
