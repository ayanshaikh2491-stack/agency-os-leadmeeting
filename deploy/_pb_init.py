"""Create PocketBase admin + core collections to mirror Supabase schema."""
import json
import urllib.request
import urllib.error

PB = "http://127.0.0.1:8090"
ADMIN_EMAIL = "admin@tagsagency.local"
ADMIN_PASS = "pb-admin-2026-x9"

def req(method, path, body=None, token=None):
    url = PB + path
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=15) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        return {"error": e.code, "body": e.read().decode()[:300]}
    except Exception as e:
        return {"error": str(e)}

# 1. create first admin (may fail if exists)
out = req("POST", "/api/admins", {"email": ADMIN_EMAIL, "password": ADMIN_PASS})
print("admin create:", json.dumps(out)[:200])

# 2. auth as admin (v0.23+ uses _superusers collection; field = identity)
out = req("POST", "/api/collections/_superusers/auth-with-password", {"identity": ADMIN_EMAIL, "password": ADMIN_PASS})
if "error" in out:
    print("admin auth FAILED:", out)
    raise SystemExit(1)
token = out["token"]
print("admin token OK:", token[:20], "...")

# 3. list existing collections
out = req("GET", "/api/collections", token=token)
names = [c.get("name") for c in out.get("items", [])]
print("existing collections:", names)

def field(name, ftype, **kw):
    f = {"name": name, "type": ftype, "required": kw.get("required", False), "system": False}
    if ftype == "text":
        f["max"] = kw.get("max", 0)
    if ftype == "number":
        f["min"] = kw.get("min")
        f["max"] = kw.get("max")
        f["noDecimals"] = kw.get("noDecimals", False)
    if ftype == "select":
        f["maxSelect"] = 1
        f["values"] = kw.get("values", [])
    if ftype == "bool":
        f["onlyFalse"] = False
    if ftype == "json":
        f["maxSize"] = kw.get("maxSize", 4000000)
    return f

def ensure_collection(name, fields, list_rule=None, create_rule=None, update_rule=None, delete_rule=None):
    if name in names:
        print("  exists:", name)
        return
    schema = []
    for f in fields:
        schema.append(field(f["name"], f["type"], **f.get("opts", {})))
    body = {
        "name": name,
        "type": "base",
        "fields": schema,
        "indexes": [],
        "listRule": list_rule,
        "viewRule": list_rule,
        "createRule": create_rule,
        "updateRule": update_rule,
        "deleteRule": delete_rule,
        "options": {"allowCreate": True},
    }
    out = req("POST", "/api/collections", body, token=token)
    if "error" in out:
        print("  CREATE FAILED", name, out)
    else:
        print("  created:", name)

print("creating collections...")
# public.leads
ensure_collection("leads", [
    {"name": "client_id", "type": "text"},
    {"name": "name", "type": "text", "opts": {"required": True}},
    {"name": "has_website", "type": "bool"},
    {"name": "phone", "type": "text"},
    {"name": "category", "type": "text"},
    {"name": "city_state", "type": "text"},
    {"name": "address", "type": "text"},
    {"name": "href", "type": "text"},
    {"name": "text", "type": "text"},
    {"name": "mode", "type": "text"},
    {"name": "website_status", "type": "text"},
    {"name": "status", "type": "select", "opts": {"values": ["candidate","good","verified","contacted","closed"]}},
    {"name": "raw", "type": "json"},
    {"name": "email", "type": "email"},
    {"name": "workspace_name", "type": "text"},
    {"name": "email_provenance", "type": "text"},
    {"name": "website", "type": "url"},
])
# workspace agent tables (mirrored in each ws schema, but PocketBase = single set)
for t in ["agent_memory", "agent_messages", "agent_data", "agent_checkpoints", "agent_checkpoint_writes"]:
    ensure_collection(t, [
        {"name": "agent_name", "type": "text"},
        {"name": "thread_id", "type": "text"},
        {"name": "checkpoint_id", "type": "text"},
        {"name": "task_id", "type": "text"},
        {"name": "memory_key", "type": "text"},
        {"name": "data_key", "type": "text"},
        {"name": "role", "type": "text"},
        {"name": "content", "type": "text"},
        {"name": "value", "type": "json"},
        {"name": "payload", "type": "json"},
        {"name": "meta", "type": "json"},
        {"name": "checkpoint", "type": "json"},
        {"name": "metadata", "type": "json"},
        {"name": "writes", "type": "json"},
        {"name": "parent_checkpoint_id", "type": "text"},
    ])

print("DONE")
