"""Sync local leads files -> self-hosted Supabase (TAGS Agency).

Reads data/sba_maps_leads_live.jsonl (all candidates) and
data/sba_maps_leads_good.jsonl (verified good leads), then upserts every
record into the Supabase `leads` table using the REST API.

- Zero external dependencies (urllib only) so it always runs.
- Idempotent: existing leads (matched by name) are updated, new ones inserted.
- Reads keys from _supabase.env (generated during EC2 setup).

Usage:
    python supabase_sync.py [--dry-run]
"""
import json
import os
import sys
import urllib.request
import urllib.error

BASE = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE, "_supabase.env")
LIVE_JSONL = os.path.join(BASE, "data", "sba_maps_leads_live.jsonl")
GOOD_JSONL = os.path.join(BASE, "data", "sba_maps_leads_good.jsonl")

DEFAULT_CLIENT = "00000000-0000-0000-0000-000000000001"  # Ayan Agency


def load_env(path: str) -> dict:
    env = {}
    if not os.path.exists(path):
        print(f"[!] .env nahi mila: {path}")
        return env
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def read_jsonl(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    return out


def api(base: str, key: str, method: str, path: str, body=None, timeout=30):
    url = base.rstrip("/") + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "apikey": key,
            "Authorization": "Bearer " + key,
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode()
            return resp.status, (json.loads(raw) if raw.strip() else None)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]


def normalize_phone(p: str) -> str:
    if not p:
        return ""
    digits = "".join(ch for ch in str(p) if ch.isdigit())
    if len(digits) == 10:
        return "+1" + digits
    if len(digits) == 11 and digits.startswith("1"):
        return "+" + digits
    return str(p).strip()


def lead_payload(lead: dict, status: str) -> dict:
    return {
        "client_id": DEFAULT_CLIENT,
        "name": lead.get("name") or "Unknown",
        "has_website": bool(lead.get("has_website")),
        "phone": normalize_phone(lead.get("phone")),
        "category": lead.get("category") or "",
        "city_state": lead.get("city_state") or "",
        "address": (lead.get("address") or "").replace("Copy address", "").strip(),
        "href": lead.get("href") or "",
        "text": lead.get("text") or "",
        "mode": lead.get("mode") or "",
        "website_status": lead.get("website_status") or "",
        "status": status,
        "raw": lead,
    }


def main():
    dry = "--dry-run" in sys.argv
    env = load_env(ENV_PATH)
    base = env.get("SUPABASE_PUBLIC_URL", "http://18.213.66.136:8050")
    key = env.get("SERVICE_ROLE_KEY", "")
    if not key:
        print("[!] SERVICE_ROLE_KEY _supabase.env mein nahi hai. Pehle setup check karo.")
        return 1

    live = read_jsonl(LIVE_JSONL)
    good = read_jsonl(GOOD_JSONL)
    good_names = {g.get("name") for g in good}

    # Build unique map by name
    merged = {}
    for lead in live:
        name = lead.get("name")
        if name:
            merged[name] = lead
    for lead in good:
        name = lead.get("name")
        if name:
            merged[name] = lead  # good version wins

    print(f"Local leads: {len(live)} live, {len(good)} good, {len(merged)} unique")

    # Fetch existing leads from Supabase
    code, existing = api(base, key, "GET", "/rest/v1/leads?select=id,name,status&limit=2000")
    if code != 200:
        print(f"[!] Supabase fetch failed: HTTP {code} {existing}")
        return 1
    existing_map = {e["name"]: e for e in (existing or [])}
    print(f"Supabase mein already: {len(existing_map)} leads")

    to_insert, to_update = [], []
    for name, lead in merged.items():
        status = "good" if name in good_names else "candidate"
        payload = lead_payload(lead, status)
        if name in existing_map:
            ex = existing_map[name]
            payload["id"] = ex["id"]
            if ex.get("status") == "good" and status == "candidate":
                payload["status"] = "good"  # kabhi good se candidate mat downgrade karo
            to_update.append(payload)
        else:
            to_insert.append(payload)

    print(f"Insert karne: {len(to_insert)}, Update karne: {len(to_update)}")

    if dry:
        print("[dry-run] kuch nahi bheja")
        return 0

    # Batch insert
    if to_insert:
        code, resp = api(base, key, "POST", "/rest/v1/leads", to_insert, timeout=60)
        print(f"INSERT: HTTP {code} {str(resp)[:200]}")
        if code not in (200, 201):
            print("  partial insert fail ho sakta hai - retry karoge to update path se ho jayega")
            to_update = to_update + to_insert  # next run fix kar dega

    # Update one by one (small batches)
    if to_update:
        ok = 0
        for payload in to_update:
            lid = payload.pop("id")
            code, resp = api(base, key, "PATCH", f"/rest/v1/leads?id=eq.{lid}", payload, timeout=30)
            if code in (200, 204):
                ok += 1
            else:
                print(f"  update fail {lid} ({payload.get('name')}): HTTP {code} {str(resp)[:150]}")
        print(f"UPDATE: {ok}/{len(to_update)} done")

    # Final count
    code, resp = api(base, key, "GET", "/rest/v1/leads?select=count")
    print(f"\nSupabase total leads ab: {resp}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
