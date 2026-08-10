"""Create missing workspace agent collections in PocketBase.

For every workspace prefix that has agent_checkpoints / agent_memory
(ws_agency__, ...), ensure these exist:
  ws_<ws>__agent_messages
  ws_<ws>__agent_data
  ws_<ws>__agent_checkpoint_writes

Schema + rules are cloned from the existing ws_<ws>__agent_checkpoints
collection so the gateway can write to them exactly like the working ones.
"""
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

out = req("POST", "/api/collections/_superusers/auth-with-password",
          {"identity": ADMIN_EMAIL, "password": ADMIN_PASS})
if "error" in out:
    print("admin auth FAILED:", out)
    raise SystemExit(1)
token = out["token"]

out = req("GET", "/api/collections?perPage=200", token=token)
names = [c.get("name") for c in out.get("items", [])]
print("total collections:", len(names))

# Workspace prefixes that already have agent tables
prefixes = sorted({n.rsplit("__agent_", 1)[0] + "__" for n in names if "__agent_" in n})
print("workspace prefixes with agent tables:", prefixes)

NEEDED = ["agent_messages", "agent_data", "agent_checkpoint_writes"]

for prefix in prefixes:
    base = prefix + "agent_checkpoints"
    if base not in names:
        print("  (no base schema", base, ")")
        continue
    # clone schema + rules from agent_checkpoints
    out = req("GET", "/api/collections/" + base, token=token)
    if "error" in out:
        print("  read failed", base, out)
        continue
    src = out
    fields = [f for f in src.get("fields", []) if not f.get("system")]
    for t in NEEDED:
        cname = prefix + t
        if cname in names:
            print("  exists:", cname)
            continue
        body = {
            "name": cname,
            "type": "base",
            "fields": fields,
            "indexes": src.get("indexes", []) or [],
            "listRule": src.get("listRule"),
            "viewRule": src.get("viewRule"),
            "createRule": src.get("createRule"),
            "updateRule": src.get("updateRule"),
            "deleteRule": src.get("deleteRule"),
            "options": {"allowCreate": True},
        }
        out2 = req("POST", "/api/collections", body, token=token)
        if "error" in out2:
            print("  CREATE FAILED", cname, out2)
        else:
            print("  created:", cname)

print("DONE")
