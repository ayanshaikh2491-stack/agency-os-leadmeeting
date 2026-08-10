"""Reproduce with REAL scraped URLs matched by phone on dog groomer Las Vegas leads."""
import sys
sys.path.insert(0, ".")
import json, urllib.request, urllib.error
from admin.agency import sba_pipeline as pipe

url, key = pipe.supabase_config()
headers = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}
leads = pipe.load_leads(url, key)

# exact real URLs from the backfill SAMPLE for dog groomer Las Vegas
sites = {
    "7253049853": "http://pawwow.us/",
    "7028783770": "https://www.hairofthedoglasvegas.com/",
    "7024768640": "http://www.happyandlucky.dog/",
    "7025869600": "https://barksnbubblessalon.com/",
}

def norm(p):
    d = "".join(ch for ch in (p or "") if ch.isdigit())
    if len(d) > 10 and d.startswith("1"):
        d = d[1:]
    return d

found = 0
for l in leads:
    np_ = norm(l.get("phone") or "")
    if np_ in sites:
        found += 1
        sid = str(l.get("id"))
        body = {"website": sites[np_], "has_website": True, "website_status": "has_website"}
        req = urllib.request.Request(
            f"{url}/rest/v1/leads?id=eq.{sid}", data=json.dumps(body).encode(),
            headers=headers, method="PATCH")
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                print(sid, np_, sites[np_], "OK", resp.status)
        except urllib.error.HTTPError as e:
            print(sid, np_, sites[np_], "HTTP", e.code, "BODY:", e.read().decode()[:400])
        except Exception as e:
            print(sid, np_, sites[np_], "ERR", repr(e)[:300])
print("found leads:", found)
