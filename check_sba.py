"""Check all SBA endpoints"""
import urllib.request, json

base = "http://localhost:9002"
endpoints = [
    ("Health", "/api/health"),
    ("SBA Status", "/api/sba/status"),
    ("SBA Leads", "/api/sba/leads"),
    ("SBA Pipeline", "/api/sba/pipeline"),
]

for name, path in endpoints:
    try:
        r = urllib.request.urlopen(base + path, timeout=5)
        data = r.read().decode()
        print(f"✅ {name}")
        print(f"   {data[:300]}")
    except Exception as e:
        print(f"❌ {name} — {str(e)[:60]}")

# Also check the SBA routes file for available endpoints
print("\n--- Checking SBA route file for endpoints ---")
