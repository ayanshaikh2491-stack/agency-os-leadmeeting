"""Remote: email/status distribution + enrichment yield."""
import os, sys
sys.path.insert(0, "/home/ubuntu/sba-backend")
try:
    from dotenv import load_dotenv; load_dotenv()
except Exception:
    pass
from supabase import create_client
u = os.getenv('SUPABASE_URL', 'http://localhost:8050').rstrip('/')
k = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
if not k:
    print('NO SUPABASE KEY'); sys.exit(1)
sb = create_client(u, k)

rows = sb.table('leads').select('email,email_provenance,status,website').limit(2000).execute().data
print("leads fetched:", len(rows))

empty = [r for r in rows if not (r.get('email') or '').strip()]
have = [r for r in rows if (r.get('email') or '').strip()]
print("empty email:", len(empty), " have email:", len(have))

from collections import Counter
print("\n-- email_provenance --")
for k2, v in Counter((r.get('email_provenance') or 'NONE') for r in have).most_common(15):
    print(f"  {k2:30s} {v}")
print("\n-- status --")
for k2, v in Counter((r.get('status') or 'NONE') for r in rows).most_common(15):
    print(f"  {k2:30s} {v}")
print("\n-- sample emails --")
import random
for r in random.sample(have, min(20, len(have))):
    print("  ", r.get('email'), "| prov:", r.get('email_provenance') or '-', "| status:", r.get('status') or '-')
print("\n-- sample enriched (provenance not NONE) --")
enr = [r for r in have if r.get('email_provenance')]
for r in enr[:20]:
    print("  ", r.get('email'), "| prov:", r.get('email_provenance'))
print("enriched count:", len(enr))
