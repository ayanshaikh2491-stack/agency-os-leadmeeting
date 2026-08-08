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
        try:
            return e.code, json.loads(e.read().decode()[:500])
        except Exception:
            return e.code, e.read().decode()[:300]

s, out = req("POST", "/api/collections/_superusers/auth-with-password", {"identity": ADMIN, "password": PASS})
token = out["token"]

# inspect an existing collection that has fields (agent_checkpoints from init)
for name in ["agent_checkpoints", "leads"]:
    s, col = req("GET", f"/api/collections/{name}", token=token)
    if s == 200:
        print(f"=== {name} schema ===")
        print(json.dumps(col.get("schema", []), indent=1)[:1500])
    else:
        print(name, "GET fail", s)

# test: create a json-field collection properly and inspect it
test_col = {
    "name": "test_json_spec",
    "type": "base",
    "schema": [
        {"name": "value", "type": "json", "required": False, "system": False, "maxSize": 0},
        {"name": "name", "type": "text", "required": False, "system": False, "max": 0},
    ],
    "indexes": [],
    "listRule": "", "viewRule": "", "createRule": "", "updateRule": "", "deleteRule": "",
}
s, out = req("POST", "/api/collections", test_col, token=token)
print("create test_json_spec:", s, json.dumps(out)[:200])
if s == 200:
    cid = out["id"]
    s2, col2 = req("GET", f"/api/collections/{cid}", token=token)
    print("inspect after create:", json.dumps(col2.get("schema", []), indent=1)[:1200])
    # now patch: add one more field
    schema = col2.get("schema", [])
    schema.append({"name": "extra", "type": "json", "required": False, "system": False, "maxSize": 0})
    s3, out3 = req("PATCH", f"/api/collections/{cid}", {
        "name": "test_json_spec", "type": "base", "schema": schema,
        "indexes": [], "listRule": "", "viewRule": "", "createRule": "", "updateRule": "", "deleteRule": "",
    }, token=token)
    print("patch add field:", s3, json.dumps(out3)[:200])
    if s3 == 200:
        s4, col4 = req("GET", f"/api/collections/{cid}", token=token)
        print("schema after patch:", [f["name"] for f in col4.get("schema", [])])
    # cleanup
    req("DELETE", f"/api/collections/{cid}", token=token)
