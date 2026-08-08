import json
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:8050"
KEY = "sb-service-key-local"

def call(path):
    headers = {"apikey": KEY, "Authorization": "Bearer " + KEY}
    req = urllib.request.Request(BASE + path, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]

for q in ["select=id,status,name&id=eq.wwzqdh2v6c5wis7",
          "select=id,status,name&status=eq.candidate",
          "select=id,status,name&status=eq.contacted"]:
    s, b = call("/rest/v1/leads?" + q)
    print(q, "->", s, json.dumps(b)[:250] if isinstance(b, list) else b)
