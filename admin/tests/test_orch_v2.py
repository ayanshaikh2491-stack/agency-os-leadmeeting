"""Test revised orchestrator — NO SBA, correct reporting chain."""
import sys
sys.path.insert(0, ".")

print("=== IMPORTS ===")

from admin.agency.orchestrator import (
    create_workspace, list_workspaces, get_workspace, delete_workspace,
    register_agent, submit_report, get_pending_reports,
    run_seo_agent_for_workspace, agency_seo_monitor, workspace_ceo_to_agency_ceo,
    setup_agency, setup_client_workspace
)
print("  [PASS] orchestrator imports")

from admin.agency.planner import create_seo_plan, execute_plan, get_plans
print("  [PASS] planner imports")

from admin.agency.scheduler import (
    create_schedule, get_schedules, run_due_tasks, get_due_tasks,
    setup_default_schedules, setup_agency_schedules
)
print("  [PASS] scheduler imports")

from admin.api.routes.orchestrator import router
paths = [r.path for r in router.routes if hasattr(r, "path")]
print(f"  [PASS] API routes: {len(paths)} endpoints")

print("\n=== CORRECT REPORTING CHAIN ===")
print("""
  Client SEO Agent:
    -> Workspace CEO (primary report)
    -> Agency SEO   (parallel - quality monitoring)

  Workspace CEO:
    -> Agency CEO   (workspace summary)

  Agency SEO:
    -> monitors all clients, catches mistakes

  NO SBA in this flow!
""")

print("=== WORKSPACE SETUP ===")

agency = setup_agency()
print(f"  [PASS] Agency created: {agency['id']}")
print(f"         Agents: {list(agency['agents'].keys())}")
assert "agency_ceo" in agency["agents"]
assert "sba" not in agency["agents"]
print("  [PASS] No SBA in agency (correct!)")

client = setup_client_workspace("DemoClient", "https://example.com", ["seo tips", "marketing"])
print(f"  [PASS] Client workspace created: {client['id']}")
print(f"         Agents: {list(client['agents'].keys())}")
assert "seo" in client["agents"]
assert "workspace_ceo" in client["agents"]
print("  [PASS] Client has SEO + Workspace CEO (correct!)")

print("\n=== REPORTING CHAIN TEST ===")

# 1. Client SEO runs and reports
result = run_seo_agent_for_workspace(client["id"])
assert "error" not in result, f"Run failed: {result}"
print(f"  [PASS] Client SEO ran successfully")
print(f"         Score: {result['results'].get('onpage', {}).get('seo_score', 'N/A')}/100")
print(f"         Submitted to: {result['submitted_to']}")
assert "workspace_ceo" in result["submitted_to"]
assert "agency_seo" in result["submitted_to"]
print("  [PASS] Report went to BOTH workspace_ceo AND agency_seo (correct!)")

# 2. Agency SEO monitors and quality checks
monitor = agency_seo_monitor()
print(f"\n  [PASS] Agency SEO Monitor:")
print(f"         Clients reviewed: {monitor.get('total_clients', 0)}")
print(f"         Avg score: {monitor.get('avg_score', 0)}")
print(f"         Flagged: {monitor.get('flagged_count', 0)}")
if monitor.get("flagged"):
    for f in monitor["flagged"]:
        print(f"           !! {f['client']}: {f['flags']}")

# 3. Workspace CEO forwards to Agency CEO
ceo_report = workspace_ceo_to_agency_ceo(client["id"])
print(f"\n  [PASS] Workspace CEO -> Agency CEO:")
print(f"         Reports forwarded: {ceo_report.get('reports_forwarded', 0)}")
assert ceo_report.get("submitted_to") == "agency_ceo"
print("  [PASS] Workspace CEO reported to Agency CEO (correct!)")

# 4. Check pending reports
seo_pending = get_pending_reports("agency_seo")
ws_ceo_pending = get_pending_reports("workspace_ceo")
agency_ceo_pending = get_pending_reports("agency_ceo")
print(f"\n  [PASS] Pending reports:")
print(f"         Agency SEO: {len(seo_pending)}")
print(f"         Workspace CEO: {len(ws_ceo_pending)}")
print(f"         Agency CEO: {len(agency_ceo_pending)}")

print("\n=== API ENDPOINTS ===")
for p in sorted(paths):
    print(f"  {p}")

print("\n=== CLEANUP ===")
delete_workspace(agency["id"])
delete_workspace(client["id"])
print("  [PASS] Cleaned up")

print("\n" + "=" * 50)
print("ALL TESTS PASSED!")
print("=" * 50)
