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
        return e.code, e.read().decode()[:400]

s, out = req("POST", "/api/collections/_superusers/auth-with-password", {"identity": ADMIN, "password": PASS})
token = out["token"]

# find a lead record id
s, recs = req("GET", "/api/collections/leads/records?perPage=3", token=token)
items = recs.get("items", [])
print("lead ids:", [i["id"] for i in items])
if items:
    rid = items[0]["id"]
    # try filter id = '...'
    import urllib.parse
    f = urllib.parse.quote(f"id = '{rid}'")
    s2, r2 = req("GET", f"/api/collections/leads/records?filter={f}", token=token)
    print("filter id eq:", s2, "count:", len(r2.get("items", [])) if isinstance(r2, dict) else r2)
    # try without quotes (numbers?)
    f3 = urllib.parse.quote(f"id = {rid}")
    s3, r3 = req("GET", f"/api/collections/leads/records?filter={f3}", token=token)
    print("filter id num:", s3, "count:", len(r3.get("items", [])) if isinstance(r3, dict) else r3)
    # try PATCH directly by path
    s4, r4 = req("PATCH", f"/api/collections/leads/records/{rid}", {"status": "contacted"}, token=token)
    print("patch by path:", s4, "status:", (r4 or {}).get("status") if isinstance(r4, dict) else r4)
