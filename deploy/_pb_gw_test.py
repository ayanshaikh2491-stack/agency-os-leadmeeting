"""End-to-end test: backend-style Supabase calls through the gateway.
Usage: GW_BASE=http://127.0.0.1:8095 GW_KEY=<service-key> python _pb_gw_test.py
"""
import json
import os
import urllib.request
import urllib.error

BASE = os.getenv("GW_BASE", "http://127.0.0.1:8050")
KEY = os.getenv("GW_KEY", "sb-service-key-local")

def call(method, path, body=None, profile=None):
    headers = {"apikey": KEY, "Authorization": "Bearer " + KEY, "Content-Type": "application/json"}
    if profile:
        headers["Content-Profile"] = profile
    if body is not None and method in ("POST", "PATCH"):
        headers["Prefer"] = "return=representation,resolution=merge-duplicates"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read().decode()
            return r.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]
    except Exception as e:
        return "ERR", str(e)

ok = True

# 1. auth check
s, b = call("GET", "/api/health")
print("health:", s, b)
if b.get("ok") is not True:
    ok = False

# 2. POST lead (like sba_pipeline saves a lead)
s, b = call("POST", "/rest/v1/leads", {
    "name": "Test Biz", "email": "test@example.com", "status": "candidate",
    "category": "restaurant", "workspace_name": "agency",
})
print("POST lead:", s, json.dumps(b)[:200] if b else b)
lead_id = None
if isinstance(b, list) and b:
    lead_id = b[0].get("id")
else:
    ok = False
if not lead_id:
    ok = False

# 2b. POST lead carrying a Supabase UUID id -> must NOT 500 (legacy_id remap)
s, b = call("POST", "/rest/v1/leads", {
    "id": "b0f3c1e2-0000-4000-8000-000000000001",
    "name": "Id Test", "email": "id@example.com",
})
print("POST lead w/ UUID id:", s, json.dumps(b)[:200] if b else b)
if s not in (200, 201) or not (isinstance(b, list) and b and b[0].get("legacy_id") == "b0f3c1e2-0000-4000-8000-000000000001"):
    print("  -> FAIL: expected legacy_id remap, got", s, b)
    ok = False

# 2c. POST lead carrying an integer id -> must NOT 500 (legacy_id remap)
s, b = call("POST", "/rest/v1/leads", {
    "id": 42, "name": "Int Id Test", "email": "intid@example.com",
})
print("POST lead w/ int id:", s, json.dumps(b)[:200] if b else b)
if s not in (200, 201) or not (isinstance(b, list) and b and b[0].get("legacy_id") == 42):
    print("  -> FAIL: expected int legacy_id remap, got", s, b)
    ok = False

# 3. GET leads (like load_leads: select=*&order=created_at.asc) — NO limit => ALL rows
s, b = call("GET", "/rest/v1/leads?select=*&order=created_at.asc")
print("GET leads (no limit):", s, "count=", len(b) if isinstance(b, list) else b)
if not (isinstance(b, list) and len(b) >= 1):
    ok = False

# 3b. GET leads with explicit limit=2 -> at most 2 rows (PostgREST semantics)
s, b = call("GET", "/rest/v1/leads?select=id&limit=2")
print("GET leads limit=2:", s, "count=", len(b) if isinstance(b, list) else b)
if not (isinstance(b, list) and len(b) == 2):
    ok = False

# 3c. GET leads with limit=1000 -> must return all rows (cap is gone; pages internally)
s, b = call("GET", "/rest/v1/leads?select=id&limit=1000")
print("GET leads limit=1000:", s, "count=", len(b) if isinstance(b, list) else b)
if not (isinstance(b, list) and len(b) >= 3):
    ok = False

# 4. PATCH lead (like sb_patch_lead: ?id=eq.{sid})
if lead_id:
    s, b = call("PATCH", f"/rest/v1/leads?id=eq.{lead_id}", {"status": "contacted"})
    print("PATCH lead:", s, json.dumps(b)[:150] if b else b)
    if not (isinstance(b, list) and b and b[0].get("status") == "contacted"):
        ok = False

# 5. agent_memory upsert (like save_memory with on_conflict + profile)
s, b = call("POST", "/rest/v1/agent_memory?on_conflict=agent_name,memory_key",
            {"agent_name": "seo", "memory_key": "k1", "value": {"a": 1}}, profile="ws_agency")
print("POST memory (ws_agency):", s, json.dumps(b)[:200] if b else b)

# upsert same key -> should update, not duplicate
s, b = call("POST", "/rest/v1/agent_memory?on_conflict=agent_name,memory_key",
            {"agent_name": "seo", "memory_key": "k1", "value": {"a": 2}}, profile="ws_agency")
print("POST memory again:", s, json.dumps(b)[:200] if b else b)

# 6. GET memory with profile + filter
s, b = call("GET", "/rest/v1/agent_memory?select=value&agent_name=eq.seo&memory_key=eq.k1", profile="ws_agency")
print("GET memory:", s, json.dumps(b)[:200] if b else b)
if not (isinstance(b, list) and b and b[0].get("value", {}).get("a") == 2):
    ok = False

# 7. agent_checkpoints (like SupabaseSaver._storage_put)
s, b = call("POST", "/rest/v1/agent_checkpoints?on_conflict=agent_name,thread_id,checkpoint_id",
            {"agent_name": "sba", "thread_id": "t1", "checkpoint_id": "c1",
             "checkpoint": {"step": 1}, "metadata": {"x": 1}}, profile="ws_agency")
print("POST checkpoint:", s, json.dumps(b)[:150] if b else b)

s, b = call("GET", "/rest/v1/agent_checkpoints?select=*&agent_name=eq.sba&thread_id=eq.t1&order=created_at.desc&limit=1", profile="ws_agency")
print("GET checkpoint:", s, json.dumps(b)[:250] if b else b)
if not (isinstance(b, list) and b and b[0].get("checkpoint", {}).get("step") == 1):
    ok = False

# 8. DELETE
if lead_id:
    s, b = call("DELETE", f"/rest/v1/leads?id=eq.{lead_id}")
    print("DELETE lead:", s, b)
    if s != 204:
        ok = False

# 9. auth reject (wrong key)
bad = urllib.request.Request(BASE + "/rest/v1/leads", headers={"apikey": "wrong"}, method="GET")
try:
    urllib.request.urlopen(bad, timeout=10)
    print("AUTH: not rejected (BAD)")
    ok = False
except urllib.error.HTTPError as e:
    print("AUTH reject:", e.code, "(good)" if e.code == 401 else "(BAD)")
    if e.code != 401:
        ok = False

print("\nRESULT:", "ALL PASS" if ok else "FAILURES FOUND")
