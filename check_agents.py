"""Check live agents on server: /api/agents (backend) + PocketBase agents collection."""
import json
import urllib.request

BASE = "http://18.213.66.136:8000"

def get(url):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())

# 1. Backend /api/agents
try:
    d = get(f"{BASE}/api/agents")
    print("== /api/agents (backend) ==")
    for a in d.get("agents", []):
        print(f"  {a['id']} | {a['name']} | {a.get('status')}")
except Exception as e:
    print("backend agents error:", e)

# 2. PocketBase agents collection
try:
    pb = get(f"{BASE}/api/collections/agents/records?perPage=200")
    print("\n== PocketBase agents collection ==")
    for a in pb.get("items", []):
        print(f"  {a.get('id')} | {a.get('slug')} | {a.get('name')}")
except Exception as e:
    print("pb agents error:", e)
