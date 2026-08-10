#!/usr/bin/env python3
"""Deduplicate PocketBase records by legacy_id (keep oldest created_at)."""
import json
import urllib.request

tok = ""
req = urllib.request.Request(
    "http://127.0.0.1:8090/api/collections/_superusers/auth-with-password",
    data=json.dumps({"identity": "admin@tagsagency.local", "password": "pb-admin-2026-x9"}).encode(),
    headers={"Content-Type": "application/json"}, method="POST")
with urllib.request.urlopen(req, timeout=15) as r:
    tok = json.loads(r.read().decode()).get("token", "")

def api(method, url):
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + tok}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = r.read().decode()
            return r.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:200]

def get_all(c):
    out = []
    page = 1
    while True:
        u = f"http://127.0.0.1:8090/api/collections/{c}/records?perPage=200&page={page}"
        s, d = api("GET", u)
        if s != 200 or not d:
            break
        items = d.get("items", [])
        out.extend(items)
        if len(items) < 200:
            break
        page += 1
    return out

for c in ["leads", "ws_agency__leads"]:
    recs = get_all(c)
    by_id = {}
    for rec in recs:
        lid = str(rec.get("legacy_id", ""))
        if not lid or lid == "None":
            continue
        by_id.setdefault(lid, []).append(rec)
    removed = 0
    for lid, group in by_id.items():
        if len(group) < 2:
            continue
        # keep oldest created_at; delete the rest
        group.sort(key=lambda r: (r.get("created_at") or ""))
        for dup in group[1:]:
            s, m = api("DELETE", f"http://127.0.0.1:8090/api/collections/{c}/records/{dup['id']}")
            if s in (200, 204):
                removed += 1
            else:
                print(f"  DEL ERR {c} {dup['id']}: {s} {m}")
    print(f"{c}: total={len(recs)} dedup_removed={removed}")
