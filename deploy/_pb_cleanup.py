"""Delete all our collections so they get recreated fresh with fields key."""
import json
import urllib.request
import urllib.error

PB = "http://127.0.0.1:8090"
ADMIN = "admin@tagsagency.local"
PASS = "pb-admin-2026-x9"
OURS = {"leads", "agent_memory", "agent_messages", "agent_data",
        "agent_checkpoints", "agent_checkpoint_writes",
        "ws_agency__leads", "ws_agency__agent_memory", "ws_agency__agent_messages",
        "ws_agency__agent_data", "ws_agency__agent_checkpoints", "ws_agency__agent_checkpoint_writes",
        "ws_default__agent_memory", "ws_default__agent_messages", "ws_default__agent_data",
        "ws_default__agent_checkpoints", "ws_default__agent_checkpoint_writes"}

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
        return e.code, None

s, out = req("POST", "/api/collections/_superusers/auth-with-password", {"identity": ADMIN, "password": PASS})
token = out["token"]

s, cols = req("GET", "/api/collections?perPage=200", token=token)
for c in cols.get("items", []):
    name = c.get("name", "")
    if name in OURS or name.startswith("ws_") or name == "test_json_spec":
        s2, _ = req("DELETE", f"/api/collections/{c['id']}", token=token)
        print("deleted:", name, s2)
print("DONE")
