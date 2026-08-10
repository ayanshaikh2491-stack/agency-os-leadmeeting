import urllib.request, json

KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
for url in ["http://127.0.0.1:8095/rest/v1/leads", "http://127.0.0.1:8095/api/health"]:
    req = urllib.request.Request(url, headers={"apikey": KEY, "Authorization": "Bearer " + KEY}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            print(url, "->", r.status, r.read().decode()[:300])
    except Exception as e:
        print(url, "-> ERR", e)
        if hasattr(e, "read"):
            print("  body:", e.read().decode()[:300])
