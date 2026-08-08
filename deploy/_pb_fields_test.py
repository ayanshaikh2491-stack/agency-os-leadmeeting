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

# verify: does create accept 'fields'?
test_col = {
    "name": "test_fields_kw",
    "type": "base",
    "fields": [
        {"name": "value", "type": "json", "required": False, "system": False, "maxSize": 0},
        {"name": "name", "type": "text", "required": False, "system": False, "max": 0},
    ],
    "indexes": [],
    "listRule": "", "viewRule": "", "createRule": "", "updateRule": "", "deleteRule": "",
}
s, out = req("POST", "/api/collections", test_col, token=token)
print("create with fields:", s, json.dumps(out)[:120])
if s == 200:
    cid = out["id"]
    s2, col2 = req("GET", f"/api/collections/{cid}", token=token)
    print("fields after create:", [f["name"] for f in col2.get("fields", [])])
    # patch adding a field using fields key
    fields = col2.get("fields", [])
    fields.append({"name": "extra2", "type": "json", "required": False, "system": False, "maxSize": 0})
    s3, out3 = req("PATCH", f"/api/collections/{cid}", {
        "name": "test_fields_kw", "type": "base", "fields": fields,
        "indexes": [], "listRule": "", "viewRule": "", "createRule": "", "updateRule": "", "deleteRule": "",
    }, token=token)
    print("patch with fields:", s3, json.dumps(out3)[:120])
    s4, col4 = req("GET", f"/api/collections/{cid}", token=token)
    print("fields after patch:", [f["name"] for f in col4.get("fields", [])])
    req("DELETE", f"/api/collections/{cid}", token=token)
