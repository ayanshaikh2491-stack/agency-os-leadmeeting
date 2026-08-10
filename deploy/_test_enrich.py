"""Test find_lead_email on 4 website+no-email leads (isolate enrichment tool)."""
import sys
sys.path.insert(0, ".")
import json, time
from admin.agency import sba_pipeline as pipe
from admin.tools.lead_enrichment import find_lead_email

url, key = pipe.supabase_config()
leads = pipe.load_leads(url, key)
ws_no_em = [l for l in leads
            if (l.get("website") or "").strip() and not (l.get("email") or "").strip()
            and (l.get("workspace_name") or "agency") == "agency"]
print("website+no-email:", len(ws_no_em))
for l in ws_no_em[:6]:
    name = (l.get("name") or "").strip()
    cs = (l.get("city_state") or "").strip()
    city = cs.split(",")[0].strip() if cs else ""
    site = (l.get("website") or "").strip()
    print("---", name, "|", city, "|", site, "| status:", l.get("status"))
    t0 = time.time()
    try:
        res = find_lead_email(name, city, l.get("category") or "", site, False, l.get("id"))
        print("   res:", json.dumps(res)[:400], f"({time.time()-t0:.0f}s)")
    except Exception as e:
        print("   ERR:", repr(e)[:200])
