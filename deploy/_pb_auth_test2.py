import json
import urllib.request
import urllib.error

def try_auth(field_name):
    body = {field_name: "admin@tagsagency.local", "password": "pb-admin-2026-x9"}
    req = urllib.request.Request(
        "http://127.0.0.1:8090/api/collections/_superusers/auth-with-password",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        r = urllib.request.urlopen(req, timeout=15)
        d = json.loads(r.read().decode())
        return "OK token=" + d.get("token", "?")[:24] + "... record=" + str(d.get("record", {}).get("email"))
    except urllib.error.HTTPError as e:
        return "ERR " + str(e.code) + " " + e.read().decode()[:250]
    except Exception as e:
        return "ERRX " + str(e)

print("email:", try_auth("email"))
print("identity:", try_auth("identity"))
