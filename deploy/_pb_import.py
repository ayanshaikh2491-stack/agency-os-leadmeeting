#!/usr/bin/env python3
"""Import Supabase JSONL exports into PocketBase via the gateway (idempotent).

Preserves legacy ids as legacy_id (PocketBase ids are 15-char). Rows whose
legacy_id already exists in PocketBase are skipped, so re-running after a
fresh export only inserts new rows.
Usage: python3 _pb_import.py <export_dir> <gateway_base> <service_key>
"""
import json
import os
import sys
import time
import urllib.request
import urllib.error

EXPORT_DIR = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/pb_export"
BASE = sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1:8095"
KEY = sys.argv[3] if len(sys.argv) > 3 else ""

PROFILES = {"ws_agency": "ws_agency", "ws_default": "ws_default", "public": None}


def api(method: str, path: str, body: dict | None = None, headers_extra: dict | None = None):
    headers = {"Content-Type": "application/json"}
    if headers_extra:
        headers.update(headers_extra)
    headers["apikey"] = KEY
    headers["Authorization"] = "Bearer " + KEY
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read().decode()
            return r.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]
    except Exception as e:  # noqa: BLE001
        return -1, str(e)[:200]


def existing_legacy_ids(table: str, profile: str | None) -> set:
    """Fetch all legacy_id values already in the target collection."""
    ids = set()
    page = 1
    while page <= 100:
        headers = {"Content-Profile": profile} if profile else None
        qs = "?select=legacy_id&limit=200&page=%d" % page
        s, data = api("GET", f"/rest/v1/{table}{qs}", headers_extra=headers)
        if s != 200 or not isinstance(data, list) or not data:
            break
        for row in data:
            if row.get("legacy_id") is not None:
                ids.add(str(row["legacy_id"]))
        if len(data) < 200:
            break
        page += 1
    return ids


def push(table: str, profile: str | None, row: dict) -> tuple[int, str]:
    body = dict(row)
    body.pop("collectionId", None)
    body.pop("collectionName", None)
    legacy = body.pop("id", None)
    if legacy is not None:
        body["legacy_id"] = legacy
    headers = {"Content-Type": "application/json"}
    if profile:
        headers["Content-Profile"] = profile
        headers["Prefer"] = "return=representation"
    s, msg = api("POST", f"/rest/v1/{table}", body, headers)
    return s, str(msg)[:120]


def main():
    total_ok = total_skip = total_err = 0
    for fname in sorted(os.listdir(EXPORT_DIR)):
        if not fname.endswith(".jsonl"):
            continue
        stem = fname[:-6]
        parts = stem.split("__", 1)
        if len(parts) == 2:
            profile, table = parts
        else:
            profile, table = "public", parts[0]
        profile = profile if profile in PROFILES else "public"
        path = os.path.join(EXPORT_DIR, fname)
        rows = []
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
        if not rows:
            print(f"{stem}: empty, skip")
            continue
        have = existing_legacy_ids(table, profile)
        ok = skip = err = 0
        t0 = time.time()
        for row in rows:
            rid = str(row.get("id", "")).strip()
            if rid and rid in have:
                skip += 1
                continue
            s, msg = push(table, profile, row)
            if s in (200, 201):
                ok += 1
            else:
                err += 1
                if err <= 3:
                    print(f"  ERR {stem} id={rid}: {s} {msg}")
        total_ok += ok
        total_skip += skip
        total_err += err
        print(f"{stem}: ok={ok} skip={skip} err={err} ({time.time()-t0:.1f}s)")
    print(f"\nDONE total_ok={total_ok} total_skip={total_skip} total_err={total_err}")


if __name__ == "__main__":
    main()
