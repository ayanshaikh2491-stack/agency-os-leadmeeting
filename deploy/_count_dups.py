#!/usr/bin/env python3
"""Count duplicate legacy_ids in PocketBase collections."""
import json
import urllib.request

tok = ""
req = urllib.request.Request(
    "http://127.0.0.1:8090/api/collections/_superusers/auth-with-password",
    data=json.dumps({"identity": "admin@tagsagency.local", "password": "pb-admin-2026-x9"}).encode(),
    headers={"Content-Type": "application/json"}, method="POST")
with urllib.request.urlopen(req, timeout=15) as r:
    tok = json.loads(r.read().decode()).get("token", "")

def get(c, page):
    u = f"http://127.0.0.1:8090/api/collections/{c}/records?perPage=200&page={page}&fields=legacy_id"
    req = urllib.request.Request(u, headers={"Authorization": "Bearer " + tok})
    return json.load(urllib.request.urlopen(req, timeout=15))

for c in ["leads", "ws_agency__leads"]:
    seen = {}
    dups = 0
    total = 0
    nolegacy = 0
    page = 1
    while True:
        d = get(c, page)
        items = d.get("items", [])
        if not items:
            break
        for it in items:
            lid = str(it.get("legacy_id", ""))
            total += 1
            if not lid or lid == "None":
                nolegacy += 1
                continue
            if lid in seen:
                dups += 1
            seen[lid] = 1
        if len(items) < 200:
            break
        page += 1
    print(f"{c}: total={total} dups={dups} no_legacy_id={nolegacy}")
