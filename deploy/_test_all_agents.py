"""Test all real agent chats to see which fail."""
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
        with urllib.request.urlopen(req, timeout=45) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() if e.fp else "{}")
    except Exception as e:
        return -1, {"error": str(e)}

agents = ["seo-engine", "content-creator", "ads-runner", "analytics-bot", "social-manager", "website-builder", "memory-agent"]
for a in agents:
    st, d = post(f"{BASE}/api/agents/{a}/chat", {"message": "Hello, introduce yourself briefly", "client_name": "Ayan Agency"})
    resp = d.get("data", {}).get("response") or d.get("response") or d.get("data", {}).get("content") or json.dumps(d)[:120]
    print(f"{a}: {st} | {str(resp)[:120]}")
