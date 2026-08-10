"""Clean junk email rows + report counts."""
import json
import urllib.error
import urllib.request

from admin.agency import sba_pipeline as pipe

url, key = pipe.supabase_config()
headers = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}

junk = pipe.sb_request(url, key, '/rest/v1/leads?select=id,name,email&email=in.("feedback@ground.news","hi@mystore.com")')
print("junk rows:", junk)
for row in junk or []:
    sid = str(row.get("id"))
    req = urllib.request.Request(
        f"{url}/rest/v1/leads?id=eq.{sid}",
        data=json.dumps({"email": None, "email_provenance": None}).encode(),
        headers=headers, method="PATCH")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            print("cleaned", sid, row.get("name"), resp.status)
    except urllib.error.HTTPError as e:
        print("clean fail", sid, e.code, e.read().decode()[:200])

all_rows = pipe.sb_request(url, key, '/rest/v1/leads?select=id,website,email')
n = len(all_rows or [])
ws = sum(1 for r in all_rows or [] if r.get("website"))
em = sum(1 for r in all_rows or [] if r.get("email"))
print("total", n, "| website", ws, "| email", em)
