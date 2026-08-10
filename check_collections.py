import json
import urllib.request

BASE = "http://18.213.66.136:8000"

def get(url):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())

d = get(f"{BASE}/api/collections?perPage=200")
print("== PB collections ==")
for c in d.get("items", []):
    print(f"  {c['id']} | {c['name']}")
