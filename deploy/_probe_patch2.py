"""Reproduce backfill PATCH failures on exact ids + payload."""
import sys
sys.path.insert(0, ".")
import json, urllib.request, urllib.error
from admin.agency import sba_pipeline as pipe

url, key = pipe.supabase_config()
headers = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}

ids = [243, 247, 252, 253, 264, 268, 293, 299]
for sid in ids:
    body = {"website": "https://repro.test/", "has_website": True, "website_status": "has_website"}
    req = urllib.request.Request(
        f"{url}/rest/v1/leads?id=eq.{sid}", data=json.dumps(body).encode(),
        headers=headers, method="PATCH")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            print(sid, "OK", resp.status)
    except urllib.error.HTTPError as e:
        print(sid, "HTTP", e.code, "BODY:", e.read().decode()[:300])
    except Exception as e:
        print(sid, "ERR", repr(e))
