"""Test all /api/sba/* endpoints live to find frontend error + check workspaces."""
import json
import urllib.request

BASE = "http://18.213.66.136:8000"

def get(url, timeout=25):
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode()[:500]
    except urllib.error.HTTPError as e:
        return e.code, (e.read().decode()[:300] if e.fp else "")
    except Exception as e:
        return -1, str(e)[:200]

def post(url, payload, timeout=40):
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode()[:600]
    except urllib.error.HTTPError as e:
        return e.code, (e.read().decode()[:300] if e.fp else "")
    except Exception as e:
        return -1, str(e)[:200]

print("== /api/sba/* endpoints ==")
for path in ["/api/sba/status", "/api/sba/pipeline", "/api/sba/meetings", "/api/sba/finance", "/api/sba/agents", "/api/sba/platforms", "/api/sba/health"]:
    st, body = get(f"{BASE}{path}")
    print(f"{path}: {st} | {body[:160]}")

print("\n== POST /api/sba/chat ==")
st, body = post(f"{BASE}/api/sba/chat", {"message": "hi", "session_id": "probe2"})
print(f"chat: {st} | {body[:200]}")

print("\n== workspaces ==")
st, body = get(f"{BASE}/api/workspaces")
print(f"workspaces: {st} | {body[:800]}")
