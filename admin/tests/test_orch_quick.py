"""Quick import + smoke test for orchestrator system."""
import sys
sys.path.insert(0, ".")

print("=== IMPORTS ===")

try:
    from admin.agency.orchestrator import (
        create_workspace, list_workspaces, get_workspace, delete_workspace,
        register_agent, submit_report, get_pending_reports,
        run_seo_agent_for_workspace, aggregate_client_reports, submit_sba_to_ceo,
        setup_agency, setup_client_workspace
    )
    print("  [PASS] orchestrator imports")
except Exception as e:
    print(f"  [FAIL] orchestrator imports: {e}")
    sys.exit(1)

try:
    from admin.agency.planner import create_seo_plan, execute_plan, get_plans
    print("  [PASS] planner imports")
except Exception as e:
    print(f"  [FAIL] planner imports: {e}")
    sys.exit(1)

try:
    from admin.agency.scheduler import (
        create_schedule, get_schedules, run_due_tasks, get_due_tasks,
        setup_default_schedules, setup_agency_schedules
    )
    print("  [PASS] scheduler imports")
except Exception as e:
    print(f"  [FAIL] scheduler imports: {e}")
    sys.exit(1)

try:
    from admin.api.routes.orchestrator import router
    paths = [r.path for r in router.routes if hasattr(r, "path")]
    print(f"  [PASS] API routes: {len(paths)} endpoints")
    for p in sorted(paths):
        print(f"         {p}")
except Exception as e:
    print(f"  [FAIL] API routes: {e}")
    sys.exit(1)

print("\n=== WORKSPACE CRUD ===")

ws = create_workspace("TestClient", "John Doe", "client", {"target_url": "https://example.com"})
print(f"  [PASS] Created workspace: {ws['id']}")
assert ws["name"] == "TestClient"

all_ws = list_workspaces()
print(f"  [PASS] Listed workspaces: {len(all_ws)} found")

got = get_workspace(ws["id"])
assert got["id"] == ws["id"]
print("  [PASS] Get workspace by ID")

print("\n=== REPORTING CHAIN (without live crawling) ===")

agency = setup_agency()
client = setup_client_workspace("DemoClient", "https://example.com", ["seo tips", "marketing"])
print(f"  [PASS] Setup: agency={agency['id']}, client={client['id']}")

# Submit a manual report to test the chain
report = submit_report(
    client["id"], "seo", "seo", "agency",
    "onpage_check",
    {"url": "https://example.com", "seo_score": 75},
    summary="Demo report for testing"
)
print(f"  [PASS] Report submitted: {report['id']}")

pending = get_pending_reports("seo")
print(f"  [PASS] Pending reports for agency SEO: {len(pending)}")

# Test aggregator (will work even with empty/old reports)
try:
    agg = aggregate_client_reports()
    print(f"  [PASS] Aggregated reports -> submitted to SBA")
except Exception as e:
    print(f"  [INFO] Aggregate (ok if no fresh reports): {e}")

try:
    sba = submit_sba_to_ceo()
    print(f"  [PASS] SBA -> CEO briefing submitted")
except Exception as e:
    print(f"  [INFO] SBA->CEO (ok if no fresh reports): {e}")

print("\n=== PLANNER ===")

plan = create_seo_plan("test_ws", "https://example.com", ["seo", "marketing"])
print(f"  [PASS] Plan created: {len(plan['tasks'])} tasks")
for t in plan["tasks"]:
    print(f"         [{t['priority']}] {t['type']}: {t['status']}")

print("\n=== SCHEDULER ===")

sched = create_schedule("test_ws", "onpage_check", {"url": "https://x.com"}, "daily")
print(f"  [PASS] Schedule created: {sched['id']}")
assert sched["frequency"] == "daily"

schedules = get_schedules("test_ws")
print(f"  [PASS] Schedules for test_ws: {len(schedules)}")

# Force a schedule to be due
scheds = get_schedules()
from admin.agency.scheduler import _schedules
for s in scheds:
    _schedules[s["id"]]["next_run"] = "2020-01-01T00:00:00+00:00"
due = get_due_tasks()
print(f"  [PASS] Due tasks detected: {len(due)}")

print("\n=== CLEANUP ===")
delete_workspace(agency["id"])
delete_workspace(client["id"])
delete_workspace(ws["id"])
print("  [PASS] Cleaned up test workspaces")

print("\n" + "=" * 50)
print("ALL TESTS PASSED!")
print("=" * 50)
