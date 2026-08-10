import os, sys
sys.path.insert(0, "/home/ubuntu/sba-backend")
try:
    from dotenv import load_dotenv; load_dotenv()
except Exception: pass
import requests
BASE = os.getenv('SUPABASE_URL', 'http://localhost:8050').rstrip('/')
KEY = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
HDRS = {"apikey": KEY, "Authorization": "Bearer " + KEY}
r = requests.get(f"{BASE}/rest/v1/leads", params={"select": "email,email_provenance,website", "limit": 2000}, headers=HDRS, timeout=30)
rows = r.json()
tot = len(rows)
with_email = [x for x in rows if (x.get('email') or '').strip()]
no_email_with_site = [x for x in rows if not (x.get('email') or '').strip() and (x.get('website') or '').strip()]
no_email_no_site = [x for x in rows if not (x.get('email') or '').strip() and not (x.get('website') or '').strip()]
prov = {}
for x in with_email:
    p = x.get('email_provenance') or 'none'
    prov[p] = prov.get(p, 0) + 1
print(f"total={tot} with_email={len(with_email)} no_email_with_site={len(no_email_with_site)} no_email_no_site={len(no_email_no_site)}")
print("provenance:", prov)
