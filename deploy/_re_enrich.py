"""Remote: re-enrich website-having no-email leads with the fixed gate.

Bypasses the 24h cooldown (one-off backfill after the prefix fix).
Uses direct REST calls (no supabase module) so it runs under venv/bin/python,
matching the autopilot service environment.
"""
import os, sys, json, time, asyncio
sys.path.insert(0, "/home/ubuntu/sba-backend")
try:
    from dotenv import load_dotenv; load_dotenv()
except Exception:
    pass
import requests

BASE = os.getenv('SUPABASE_URL', 'http://localhost:8050').rstrip('/')
KEY = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
if not KEY:
    print("NO SUPABASE KEY"); sys.exit(1)
HDRS = {"apikey": KEY, "Authorization": "Bearer " + KEY}

def fetch_leads(limit=2000):
    r = requests.get(f"{BASE}/rest/v1/leads",
                     params={"select": "id,name,email,website,city_state,category,email_provenance",
                             "limit": limit},
                     headers=HDRS, timeout=30)
    r.raise_for_status()
    return r.json()

rows = fetch_leads()
no_email_with_site = [x for x in rows if not (x.get('email') or '').strip() and (x.get('website') or '').strip()]
print(f"no-email leads WITH website: {len(no_email_with_site)}", flush=True)

from admin.tools.lead_enrichment import find_lead_email
from admin.agency.sba_autopilot import _is_valid_lead_email

found = []
skipped = []
failed = 0
sem = asyncio.Semaphore(4)

def patch_email(lid, email, prov):
    try:
        r = requests.patch(f"{BASE}/rest/v1/leads?id=eq.{lid}",
                           json={"email": email, "email_provenance": prov},
                           headers={**HDRS, "Content-Type": "application/json",
                                    "Prefer": "return=minimal"},
                           timeout=15)
        return r.status_code in (200, 201, 204)
    except requests.RequestException:
        return False

def enrich_one(lead):
    name = (lead.get("name") or "").strip()
    if not name:
        return
    cs = (lead.get("city_state") or "").strip()
    city = cs.split(",")[0].strip() if cs else ""
    site = (lead.get("website") or "").strip()
    try:
        res = find_lead_email(name, city, lead.get("category") or "", site, False, lead.get("id"))
        email = (res or {}).get("email") or ""
        prov = (res or {}).get("provenance") or ""
        if email and _is_valid_lead_email(email, allow_consumer=(prov in ("consumer", "own_domain", "homepage"))):
            ok = patch_email(lead.get("id"), email, prov)
            found.append((name, email, prov))
            print(f"  EMAIL {name} -> {email} ({prov}, patched={ok})", flush=True)
        elif email:
            skipped.append((name, email, prov))
            print(f"  SKIP {name} -> {email} ({prov})", flush=True)
        else:
            print(f"  none: {name}", flush=True)
    except Exception as e:
        global failed
        failed += 1
        print(f"  FAIL {name}: {e}", flush=True)

async def run_one(lead):
    async with sem:
        await asyncio.wait_for(asyncio.to_thread(enrich_one, lead), timeout=120)

async def main():
    await asyncio.gather(*(run_one(l) for l in no_email_with_site))
    print(f"\nRESULT found={len(found)} skipped={len(skipped)} failed={failed} total_tried={len(no_email_with_site)}", flush=True)

asyncio.run(main())
