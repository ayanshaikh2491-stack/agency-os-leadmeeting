"""Test agent chat + SBA chat via Vercel proxy (end-to-end frontend path)."""
import json, urllib.request, urllib.error, sys

BASE = "https://agency-frontend-seven.vercel.app"

def post(path, body, timeout=90):
    data = json.dumps(body).encode()
    req = urllib.request.Request(BASE + path, data=data,
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode()
            try:
                return resp.status, json.loads(raw)
            except Exception:
                return resp.status, {"raw": raw[:300]}
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:500]
    except Exception as e:
        return -1, {"err": str(e)[:300]}

st, d = post("/api/agents/seo-engine/chat", {"message": "hi, one line status", "client_name": "Agency Workspace"})
print("seo-engine via Vercel:", st)
print(json.dumps(d)[:500])

st, d = post("/api/sba/chat", {"message": "hi, one line status"})
print("\nsba chat via Vercel:", st)
print(json.dumps(d)[:500])
