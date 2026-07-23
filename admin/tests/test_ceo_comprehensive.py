"""Comprehensive test for CEO agent upgrade — all interview requirements."""
import sys
sys.path.insert(0, r"C:\Users\TAUSHEF\Downloads\int")

errors = []

# ── Test 1: CEO Agent Import ──
print("=== Test 1: CEO Agent Import ===")
try:
    from admin.agency.ceo import AgencyCEO, CEO_TOOLS, CEO_SYSTEM_PROMPT, CEOGraphState
    ceo = AgencyCEO()
    print(f"  OK - {len(CEO_TOOLS)} tools loaded")
    assert len(CEO_TOOLS) >= 9, f"Expected 9+ tools, got {len(CEO_TOOLS)}"
    print("  OK - CEO agent initialized")
except Exception as e:
    errors.append(f"CEO import: {e}")
    print(f"  FAIL: {e}")

# ── Test 2: Co-founder persona in prompt (Q19) ──
print("\n=== Test 2: Co-founder Persona (Q19) ===")
assert "co-founder" in CEO_SYSTEM_PROMPT.lower(), "Missing co-founder persona"
assert "disagree" in CEO_SYSTEM_PROMPT.lower(), "Missing disagree/disrespectful behavior"
assert "candid" in CEO_SYSTEM_PROMPT.lower() or "direct" in CEO_SYSTEM_PROMPT.lower(), "Missing candid/direct"
print("  OK - Co-founder persona confirmed")

# ── Test 3: Parallel blast tool (Q4) ──
print("\n=== Test 3: Parallel Blast Tool (Q4) ===")
tool_names = [t["function"]["name"] for t in CEO_TOOLS]
assert "delegate_parallel_blast" in tool_names, "Missing parallel blast tool"
print("  OK - Parallel blast tool present")

# ── Test 4: Handoff receive tool (Q17) ──
print("\n=== Test 4: Handoff Receive (Q17) ===")
assert "receive_sba_handoff" in tool_names, "Missing handoff tool"
print("  OK - SBA handoff tool present")

# ── Test 5: Review tool (Q20) ──
print("\n=== Test 5: Agent Review (Q20) ===")
assert "review_agent_output" in tool_names, "Missing review tool"
print("  OK - Review tool present")

# ── Test 6: Error routing (Q21) ──
print("\n=== Test 6: Error Routing (Q21) ===")
assert "route_error_fix" in tool_names, "Missing error routing tool"
print("  OK - Error routing tool present")

# ── Test 7: Report generation (Q23) ──
print("\n=== Test 7: Report Generation (Q23) ===")
assert "generate_report" in tool_names, "Missing report tool"
print("  OK - Report generation tool present")

# ── Test 8: Cross-workspace knowledge (CRITICAL) ──
print("\n=== Test 8: Cross-workspace Knowledge ===")
assert "get_cross_workspace_knowledge" in tool_names, "Missing knowledge tool"
print("  OK - Cross-workspace knowledge tool present")

# ── Test 9: Workspace Manager Functions ──
print("\n=== Test 9: Workspace Manager ===")
try:
    from admin.workspace.manager import (
        store_agent_output, list_pending_reviews, store_review,
        list_reviews, store_error, list_errors
    )
    
    # Test store_agent_output
    out = store_agent_output("ws_test", "seo", "keyword research", "Found 50 keywords")
    assert out["id"].startswith("out_"), "Invalid output ID"
    print("  OK - store_agent_output works")
    
    # Test list_pending_reviews
    pending = list_pending_reviews()
    assert len(pending) >= 1, "No pending reviews"
    print(f"  OK - list_pending_reviews: {len(pending)} pending")
    
    # Test store_review
    rev = store_review("ws_test", "seo", out["id"], "approved", "Good work")
    assert rev["verdict"] == "approved", "Invalid verdict"
    print("  OK - store_review works")
    
    # Test store_error
    err = store_error("ws_test", "seo_issue", "high", "Rankings dropped 20 positions")
    assert err["id"].startswith("err_"), "Invalid error ID"
    print("  OK - store_error works")
    
    # Test list_errors
    errs = list_errors()
    assert len(errs) >= 1, "No errors listed"
    print(f"  OK - list_errors: {len(errs)} errors")
    
except Exception as e:
    errors.append(f"Workspace manager: {e}")
    print(f"  FAIL: {e}")

# ── Test 10: CEO Direct API Methods ──
print("\n=== Test 10: CEO Direct API Methods ===")
try:
    import asyncio
    
    # Test receive_handoff (with fake ID)
    result = asyncio.run(ceo.receive_handoff("fake_id", "review_only"))
    assert "not found" in result.lower(), "Should return not found for fake ID"
    print("  OK - receive_handoff works")
    
    # Test generate_report
    result = asyncio.run(ceo.generate_report("weekly"))
    assert "AGENCY" in result.upper() or "report" in result.lower(), "Invalid report"
    print("  OK - generate_report works")
    
    # Test cross_workspace_knowledge
    result = asyncio.run(ceo.cross_workspace_knowledge("add_learning", domain="seo", learning="Long-form content ranks better"))
    assert "added" in result.lower(), "Learning not added"
    print("  OK - cross_workspace_knowledge add works")
    
    result = asyncio.run(ceo.cross_workspace_knowledge("get_by_domain", domain="seo"))
    assert "long-form" in result.lower(), "Learning not retrieved"
    print("  OK - cross_workspace_knowledge get works")
    
except Exception as e:
    errors.append(f"CEO API methods: {e}")
    print(f"  FAIL: {e}")

# ── Test 11: Routes Registration ──
print("\n=== Test 11: Routes ===")
try:
    from admin.api.routes.ceo import router, _old_router
    new_routes = [r.path for r in router.routes]
    old_routes = [r.path for r in _old_router.routes]
    
    expected_routes = [
        "/api/ceo/chat", "/api/ceo/handoff/receive", "/api/ceo/parallel-blast",
        "/api/ceo/review", "/api/ceo/error/route", "/api/ceo/report",
        "/api/ceo/knowledge", "/api/ceo/reviews", "/api/ceo/errors",
    ]
    for route in expected_routes:
        assert route in new_routes, f"Missing route: {route}"
    
    assert "/api/chat/agency" in old_routes, "Missing legacy route"
    print(f"  OK - {len(new_routes)} new routes + {len(old_routes)} legacy routes")
except Exception as e:
    errors.append(f"Routes: {e}")
    print(f"  FAIL: {e}")

# ── Summary ──
print("\n" + "=" * 50)
if errors:
    print(f"FAILED: {len(errors)} errors")
    for e in errors:
        print(f"  - {e}")
else:
    print("ALL 11 TESTS PASSED!")
    print("\nCEO Agent Upgrade Summary:")
    print("  Q4  - Parallel blast delegation     DONE")
    print("  Q17 - SBA handoff receive            DONE")
    print("  Q19 - Co-founder persona             DONE")
    print("  Q20 - Agent output review            DONE")
    print("  Q21 - Error recovery routing         DONE")
    print("  Q23 - Weekly/monthly reporting        DONE")
    print("  CRIT - Cross-workspace knowledge     DONE")
