"""Test all CEO API endpoints via HTTP."""
import json
import urllib.request

BASE = "http://localhost:9002"

def get(path):
    try:
        with urllib.request.urlopen(f"{BASE}{path}") as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}

def post(path, data):
    try:
        req = urllib.request.Request(
            f"{BASE}{path}",
            data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}

# 1. Health
print("=== 1. Health ===")
r = get("/api/health")
print(f"  {r}")

# 2. CEO Chat
print("\n=== 2. CEO Chat ===")
r = post("/api/ceo/chat", {"message": "Hello, what's the agency status?"})
print(f"  Status: {r.get('status', 'N/A')}")
print(f"  Response: {r.get('response', r.get('error', 'N/A'))[:200]}")

# 3. Legacy endpoint
print("\n=== 3. Legacy /api/chat/agency ===")
r = post("/api/chat/agency", {"message": "Hello"})
print(f"  Status: {r.get('status', 'N/A')}")
print(f"  Response: {r.get('response', r.get('error', 'N/A'))[:200]}")

# 4. List Workspaces
print("\n=== 4. List Workspaces ===")
r = get("/api/workspace/list")
print(f"  {r}")

# 5. CEO Reviews
print("\n=== 5. CEO Reviews ===")
r = get("/api/ceo/reviews")
print(f"  {r}")

# 6. CEO Errors
print("\n=== 6. CEO Errors ===")
r = get("/api/ceo/errors")
print(f"  {r}")

# 7. CEO Knowledge
print("\n=== 7. CEO Knowledge ===")
r = get("/api/ceo/knowledge?action=get_all")
print(f"  {r}")

# 8. CEO Report
print("\n=== 8. CEO Report (weekly) ===")
r = post("/api/ceo/report", {"report_type": "weekly"})
print(f"  Report: {r.get('report', r.get('error', 'N/A'))[:300]}")

# 9. CEO Parallel Blast (no workspace yet)
print("\n=== 9. CEO Parallel Blast ===")
r = post("/api/ceo/parallel-blast", {
    "workspace_id": "nonexistent",
    "client_brief": "Test client",
})
print(f"  {r}")

# 10. CEO Handoff Receive
print("\n=== 10. CEO Handoff Receive ===")
r = post("/api/ceo/handoff/receive", {
    "handoff_id": "nonexistent",
    "action": "review_only",
})
print(f"  {r}")

# 11. CEO Error Route
print("\n=== 11. CEO Error Route ===")
r = post("/api/ceo/error/route", {
    "workspace_id": "nonexistent",
    "error_type": "seo_issue",
    "severity": "high",
    "description": "Rankings dropped",
})
print(f"  {r}")

# 12. CEO Review Output
print("\n=== 12. CEO Review Output ===")
r = post("/api/ceo/review", {
    "workspace_id": "ws_test",
    "agent_type": "seo",
    "verdict": "approved",
    "feedback": "Good keyword research",
})
print(f"  {r}")

# 13. Add Knowledge
print("\n=== 13. Add Knowledge ===")
r = post("/api/ceo/knowledge", {
    "action": "add_learning",
    "domain": "ads",
    "learning": "Video ads get 3x CTR on Meta",
    "source_workspace": "ws_test",
})
print(f"  {r}")

print("\n=== ALL ENDPOINT TESTS COMPLETE ===")
