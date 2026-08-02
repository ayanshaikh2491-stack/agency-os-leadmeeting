import json, os, urllib.request

env = {}
for line in open(r"C:\Users\TAUSHEF\Downloads\int\_supabase.env", encoding="utf-8"):
    line = line.strip()
    if line and "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()

base = env["SUPABASE_PUBLIC_URL"]
key = env["SERVICE_ROLE_KEY"]

req = urllib.request.Request(
    base + "/rest/v1/leads?select=name,status,phone,category,city_state&status=eq.good",
    headers={"apikey": key, "Authorization": "Bearer " + key},
)
with urllib.request.urlopen(req, timeout=30) as r:
    good = json.loads(r.read().decode())
print("=== GOOD LEADS (with phones) ===")
for g in good:
    print(f"  {g['name']} | {g.get('phone')} | {g.get('category')} | {g.get('city_state')}")

# count with phones
req2 = urllib.request.Request(
    base + "/rest/v1/leads?select=phone",
    headers={"apikey": key, "Authorization": "Bearer " + key},
)
with urllib.request.urlopen(req2, timeout=30) as r:
    alll = json.loads(r.read().decode())
with_phone = sum(1 for l in alll if l.get("phone"))
print(f"\nTotal leads: {len(alll)}, with phone: {with_phone}")
