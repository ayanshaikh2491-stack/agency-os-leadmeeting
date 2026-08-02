import urllib.request, json, os, base64

# Read keys from local .env
env = {}
with open(r"C:\Users\TAUSHEF\Downloads\int\_supabase.env", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k] = v.strip()

anon = env["ANON_KEY"]
sr = env["SERVICE_ROLE_KEY"]
base = "http://18.213.66.136:8050"

# Test external REST with service role
req = urllib.request.Request(
    base + "/rest/v1/leads?select=name,status,phone&status=eq.good&limit=3",
    headers={"apikey": sr, "Authorization": "Bearer " + sr},
)
try:
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode())
        print("EXTERNAL good leads OK:", len(data))
        for d in data[:3]:
            print(" ", d["name"], "|", d.get("phone"))
except Exception as e:
    print("ERROR:", e)

# Count
req2 = urllib.request.Request(
    base + "/rest/v1/leads?select=count",
    headers={"apikey": sr, "Authorization": "Bearer " + sr},
)
try:
    with urllib.request.urlopen(req2, timeout=20) as resp:
        print("count:", resp.read().decode())
except Exception as e:
    print("count ERROR:", e)

# Studio reachable?
req3 = urllib.request.Request(base + "/studio/")
try:
    with urllib.request.urlopen(req3, timeout=20) as resp:
        print("Studio HTTP:", resp.status)
except Exception as e:
    print("Studio:", e)
