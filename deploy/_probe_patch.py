"""Probe: lead keys + raw PATCH error body on EC2."""
import sys
sys.path.insert(0, ".")
import json, urllib.request, urllib.error
from admin.agency import sba_pipeline as pipe

url, key = pipe.supabase_config()
leads = pipe.load_leads(url, key)
print("total:", len(leads))
if leads:
    print("KEYS:", sorted(leads[0].keys()))

# raw PATCH test: first update website only on a real row, then with website_status
if leads:
    sid = str(leads[0].get("id") or leads[0].get("lead_id") or "")
    print("test sid:", sid)
    headers = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    for label, body in [
        ("website+has_website", {"website": "https://example-probe.test/", "has_website": True}),
        ("with_website_status", {"website_status": "has_website"}),
    ]:
        req = urllib.request.Request(
            f"{url}/rest/v1/leads?id=eq.{sid}", data=json.dumps(body).encode(),
            headers=headers, method="PATCH")
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                print(label, "OK", resp.status)
        except urllib.error.HTTPError as e:
            print(label, "HTTP", e.code, "BODY:", e.read().decode()[:500])
        except Exception as e:
            print(label, "ERR", e)

    # restore: clear the probe website
    req = urllib.request.Request(
        f"{url}/rest/v1/leads?id=eq.{sid}", data=json.dumps({"website": None, "has_website": False}).encode(),
        headers=headers, method="PATCH")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            print("restore OK", resp.status)
    except urllib.error.HTTPError as e:
        print("restore HTTP", e.code, "BODY:", e.read().decode()[:300])
