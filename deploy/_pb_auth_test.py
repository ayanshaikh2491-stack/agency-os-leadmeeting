import json
import urllib.request
import urllib.error

def try_auth(body):
    req = urllib.request.Request(
        "http://127.0.0.1:8090/api/collections/_superusers/auth-with-password",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        r = urllib.request.urlopen(req, timeout=15)
        return "OK " + r.read().decode()[:200]
    except urllib.error.HTTPError as e:
        return "ERR " + str(e.code) + " " + e.read().decode()[:300]
    except Exception as e:
        return "ERRX " + str(e)

print("email+pass:", try_auth({"email": "admin@tagsagency.local", "password": "pb-admin-2026-x9"}))
print("identity+pass:", try_auth({"identity": "admin@tagsagency.local", "password": "pb-admin-2026-x9"}))

# also try listing collections without auth to see API shape
req = urllib.request.Request("http://127.0.0.1:8090/api/collections", method="GET")
try:
    r = urllib.request.urlopen(req, timeout=15)
    print("list public:", r.read().decode()[:300])
except urllib.error.HTTPError as e:
    print("list ERR:", e.code, e.read().decode()[:300])
