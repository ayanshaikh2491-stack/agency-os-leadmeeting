"""Remote: diagnose enrichment failures on website-having no-email leads."""
import os, sys, json, time
sys.path.insert(0, "/home/ubuntu/sba-backend")
try:
    from dotenv import load_dotenv; load_dotenv()
except Exception:
    pass
from supabase import create_client
u = os.getenv('SUPABASE_URL', 'http://localhost:8050').rstrip('/')
k = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
sb = create_client(u, k)

# No-email leads that HAVE a website
rows = sb.table('leads').select('id,name,email,website,city_state,category').or_('email,is.null').execute().data if False else None

# simpler: fetch leads with website, filter empty email in python
rows = sb.table('leads').select('id,name,email,website,city_state,category,email_provenance').limit(2000).execute().data
no_email_with_site = [r for r in rows if not (r.get('email') or '').strip() and (r.get('website') or '').strip()]
print("no-email leads WITH website:", len(no_email_with_site))

sys.path.insert(0, "/home/ubuntu/sba-backend")
from admin.tools.lead_enrichment import find_lead_email, ENRICH_BUDGET_SECONDS

# Test 5 of them
for r in no_email_with_site[:6]:
    name = r.get('name') or ''
    site = r.get('website') or ''
    city = (r.get('city_state') or '').split(',')[0].strip()
    cat = r.get('category') or ''
    t0 = time.time()
    try:
        res = find_lead_email(name, city, cat, website=site, patch_supabase=False)
        print(f"\n[{time.time()-t0:.1f}s] {name}")
        print(f"  site={site}")
        print(f"  email={res.get('email')!r} prov={res.get('provenance')!r} domains={res.get('domains')}")
        if res.get('all_emails'):
            print(f"  all_emails={res.get('all_emails')[:5]}")
    except Exception as e:
        print(f"\n[{time.time()-t0:.1f}s] {name} ERROR: {e}")
