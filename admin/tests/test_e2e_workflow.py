"""Full E2E workflow test — CEO + workspace creation + agent delegation."""
import json
import time
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
print("TAGS AGENCY OS — FULL E2E WORKFLOW TEST")
print("=" * 60)

# ── Step 1: Health Check ──
print("\n--- Step 1: Health Check ---")
r = get("/api/health")
print(f"  Status: {r.get('status')}")
print(f"  CEO Ready: {r.get('ceo_ready')}")

# ── Step 2: Create Workspace ──
print("\n--- Step 2: Create Workspace ---")
r = post("/api/workspace/create", {
    "name": "Acme Corp Workspace",
    "client_name": "Rahul Sharma",
    "description": "E-commerce client, needs SEO + Ads + Website"
})
print(f"  Response: {r}")
ws_id = r.get("id", "")
print(f"  Workspace ID: {ws_id}")

# ── Step 3: CEO Chat (with workspace context) ──
print("\n--- Step 3: CEO Chat ---")
r = post("/api/ceo/chat", {
    "message": "We just onboarded a new client Acme Corp. They need SEO, Ads, and a website. What's your plan?"
})
response = r.get("response", r.get("error", "N/A"))
print(f"  CEO Response: {response[:500]}")

# ── Step 4: Parallel Blast (brief all agents) ──
if ws_id:
    print("\n--- Step 4: Parallel Blast ---")
    r = post("/api/ceo/parallel-blast", {
        "workspace_id": ws_id,
        "client_brief": "Acme Corp is an e-commerce brand selling premium fitness equipment. Target audience: 25-45 urban professionals. Budget: $5000/month for ads. Need: full website redesign, SEO optimization, Meta + Google ads, social media strategy.",
        "campaign_name": "Acme Corp Launch",
        "deadline": "2026-08-15",
    })
    result = r.get("result", r.get("error", "N/A"))
    print(f"  Parallel Blast Result: {result[:800]}")

# ── Step 5: Individual Agent Delegation ──
if ws_id:
    print("\n--- Step 5: Delegate to SEO Agent ---")
    r = post("/api/ceo/chat", {
        "message": f"Delegate to SEO agent in workspace {ws_id}: Run a full SEO audit for acmecorp.com and propose a 3-month SEO strategy."
    })
    response = r.get("response", r.get("error", "N/A"))
    print(f"  CEO Response: {response[:500]}")

# ── Step 6: CEO Reviews ──
print("\n--- Step 6: CEO Reviews ---")
r = get("/api/ceo/reviews")
print(f"  Pending Reviews: {r.get('pending_count', 0)}")
print(f"  Completed Reviews: {len(r.get('completed', []))}")

# ── Step 7: CEO Errors ──
print("\n--- Step 7: CEO Errors ---")
r = get("/api/ceo/errors")
print(f"  Error Count: {r.get('count', 0)}")

# ── Step 8: CEO Report ──
print("\n--- Step 8: CEO Weekly Report ---")
r = post("/api/ceo/report", {"report_type": "weekly"})
report = r.get("report", "N/A")
print(f"  Report:\n{report[:500]}")

# ── Step 9: Add Knowledge ──
print("\n--- Step 9: Cross-Workspace Knowledge ---")
r = post("/api/ceo/knowledge", {
    "action": "add_learning",
    "domain": "seo",
    "learning": "Long-form product descriptions (2000+ words) improved rankings by 40% for e-commerce clients",
    "source_workspace": ws_id or "test",
})
print(f"  Add: {r.get('result', r.get('error', 'N/A'))[:200]}")

r = get("/api/ceo/knowledge?action=get_by_domain&domain=seo")
print(f"  Get: {r.get('knowledge', 'N/A')[:200]}")

# ── Step 10: Review Agent Output ──
print("\n--- Step 10: CEO Review Output ---")
r = post("/api/ceo/review", {
    "workspace_id": ws_id or "test",
    "agent_type": "seo",
    "verdict": "approved",
    "feedback": "Good keyword research, solid strategy. Ready for Ayan's sign-off.",
})
print(f"  Review: {r.get('result', r.get('error', 'N/A'))[:200]}")

# ── Step 11: Error Routing ──
print("\n--- Step 11: Error Routing ---")
r = post("/api/ceo/error/route", {
    "workspace_id": ws_id or "test",
    "error_type": "ads_underperforming",
    "severity": "high",
    "description": "Meta Ads CPA jumped 60% in last 3 days, ROAS dropped below 1.5x",
})
print(f"  Error Route: {r.get('result', r.get('error', 'N/A'))[:300]}")

print("\n" + "=" * 60)
print("E2E WORKFLOW TEST COMPLETE")
print("=" * 60)
