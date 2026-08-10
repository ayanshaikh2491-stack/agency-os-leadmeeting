"""Verify live after stub removal: real agent chat works, stub agent 404s, services green."""
import json
import urllib.request

BASE = "http://18.213.66.136:8000"

def post(url, payload):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() if e.fp else "{}")

# 1. Real agent chat (seo-engine)
st, d = post(f"{BASE}/api/agents/seo-engine/chat", {"message": "Hello, give me a quick status", "client_name": "Ayan Agency"})
print("seo-engine chat:", st, "| response:", str(d.get("data", {}).get("response", d))[:150])

# 2. Deleted stub agent chat should 404
st2, d2 = post(f"{BASE}/api/agents/intake-researcher/chat", {"message": "hi", "client_name": "Ayan Agency"})
print("intake-researcher chat:", st2, "| body:", json.dumps(d2)[:150])

# 3. Stub status endpoint should 404 too
req = urllib.request.Request(f"{BASE}/api/agents/sales-closer/status")
try:
    with urllib.request.urlopen(req, timeout=15) as r:
        print("sales-closer status:", r.status)
except urllib.error.HTTPError as e:
    print("sales-closer status:", e.code)

# 4. Real agent status works
req = urllib.request.Request(f"{BASE}/api/agents/seo-engine/status")
with urllib.request.urlopen(req, timeout=15) as r:
    print("seo-engine status:", r.status, r.read().decode()[:80])
