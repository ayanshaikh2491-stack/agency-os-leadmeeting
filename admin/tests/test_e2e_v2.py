"""Full E2E workflow test — corrected endpoints."""
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
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}

print("=" * 60)
print("TAGS AGENCY OS — FULL E2E WORKFLOW TEST (Fixed)")
print("=" * 60)

# ── Step 1: Health ──
print("\n--- Step 1: Health ---")
r = get("/api/health")
print(f"  {r}")

# ── Step 2: Create Workspace (correct endpoint) ──
print("\n--- Step 2: Create Workspace ---")
r = post("/api/chat/workspace", {
    "name": "Acme Corp Workspace",
    "client_name": "Rahul Sharma",
    "description": "E-commerce client, needs SEO + Ads + Website"
})
print(f"  Response: {r}")
ws_id = r.get("id", "")
print(f"  Workspace ID: {ws_id}")

# ── Step 3: List Workspaces ──
print("\n--- Step 3: List Workspaces ---")
r = get("/api/chat/workspace")
print(f"  Workspaces: {len(r) if isinstance(r, list) else r}")

# ── Step 4: CEO Chat ──
print("\n--- Step 4: CEO Chat ---")
r = post("/api/ceo/chat", {
    "message": "We just onboarded Acme Corp. They need SEO, Ads, and a website. What's your strategic plan?"
})
response = r.get("response", r.get("error", "N/A"))
print(f"  CEO: {response[:600]}")

# ── Step 5: Parallel Blast ──
if ws_id:
    print("\n--- Step 5: Parallel Blast ---")
    r = post("/api/ceo/parallel-blast", {
        "workspace_id": ws_id,
        "client_brief": "Acme Corp is an e-commerce brand selling premium fitness equipment. Target: 25-45 urban professionals. Budget: $5000/month ads. Need: website redesign, SEO, Meta+Google ads, social strategy.",
        "campaign_name": "Acme Corp Launch",
        "deadline": "2026-08-15",
    })
    result = r.get("result", r.get("error", "N/A"))
    print(f"  Result: {result[:1000]}")
else:
    print("\n--- Step 5: SKIPPED (no workspace) ---")

# ── Step 6: Delegate to Individual Agent ──
if ws_id:
    print("\n--- Step 6: Delegate to SEO Agent ---")
    r = post(f"/api/chat/workspace/{ws_id}/chat", {
        "message": "Run a full SEO audit for acmecorp.com and propose a 3-month strategy.",
        "agent_type": "seo",
    })
    print(f"  SEO Agent: {r.get('response', r.get('error', 'N/A'))[:500]}")

# ── Step 7: Reviews ──
print("\n--- Step 7: CEO Reviews ---")
r = get("/api/ceo/reviews")
print(f"  Pending: {r.get('pending_count', 0)}, Completed: {len(r.get('completed', []))}")

# ── Step 8: Report ──
print("\n--- Step 8: Weekly Report ---")
r = post("/api/ceo/report", {"report_type": "weekly"})
print(f"  {r.get('report', 'N/A')[:400]}")

# ── Step 9: Knowledge ──
print("\n--- Step 9: Knowledge ---")
r = post("/api/ceo/knowledge", {
    "action": "add_learning",
    "domain": "ads",
    "learning": "Video ads get 3x CTR on Meta for fitness brands",
    "source_workspace": ws_id or "test",
})
print(f"  {r.get('result', 'N/A')[:200]}")

print("\n" + "=" * 60)
print("E2E TEST COMPLETE")
print("=" * 60)
