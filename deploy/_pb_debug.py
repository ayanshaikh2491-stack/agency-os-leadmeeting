import json
import urllib.request
import urllib.error

PB = "http://127.0.0.1:8090"
ADMIN = "admin@tagsagency.local"
PASS = "pb-admin-2026-x9"

def req(method, path, body=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(PB + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=15) as resp:
            raw = resp.read().decode()
            return resp.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode()[:500])

s, out = req("POST", "/api/collections/_superusers/auth-with-password", {"identity": ADMIN, "password": PASS})
token = out["token"]

# check leads collection schema
s, col = req("GET", "/api/collections/leads", token=token)
print("leads schema fields:", [f["name"] + ":" + f["type"] for f in col.get("schema", [])])

# check ws_agency__agent_memory
s, col2 = req("GET", "/api/collections/ws_agency__agent_memory", token=token)
if s == 200:
    print("memory schema fields:", [f["name"] + ":" + f["type"] for f in col2.get("schema", [])])

# list records in leads
s, recs = req("GET", "/api/collections/leads/records?perPage=5", token=token)
print("leads records:", json.dumps(recs)[:500])
