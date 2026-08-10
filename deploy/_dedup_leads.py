import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

script = r'''
PB_ADMIN="admin@tagsagency.local"; PB_PASS="pb-admin-2026-x9"
TOKEN=$(curl -s -X POST http://127.0.0.1:8090/api/collections/_superusers/auth-with-password \
  -H "Content-Type: application/json" \
  -d "{\"identity\":\"$PB_ADMIN\",\"password\":\"$PB_PASS\"}" | python3 -c "import sys,json;print(json.load(sys.stdin).get('token',''))" 2>/dev/null)

# Backup + identify duplicates
curl -s -H "Authorization: $TOKEN" "http://127.0.0.1:8090/api/collections/leads__leads/records?perPage=200&page=1" > /tmp/pb_p1.json
curl -s -H "Authorization: $TOKEN" "http://127.0.0.1:8090/api/collections/leads__leads/records?perPage=200&page=2" > /tmp/pb_p2.json
curl -s -H "Authorization: $TOKEN" "http://127.0.0.1:8090/api/collections/leads__leads/records?perPage=200&page=3" > /tmp/pb_p3.json
curl -s -H "Authorization: $TOKEN" "http://127.0.0.1:8090/api/collections/leads__leads/records?perPage=200&page=4" > /tmp/pb_p4.json
curl -s -H "Authorization: $TOKEN" "http://127.0.0.1:8090/api/collections/leads__leads/records?perPage=200&page=5" > /tmp/pb_p5.json

python3 - <<'EOF'
import json, urllib.request, urllib.error

TOKEN = open("/dev/stdin").read() if False else None
# reload token from env is awkward in heredoc; use a file
EOF
'''

# Simpler: do everything in one python3 heredoc on EC2 using the gateway key
script2 = r'''
cd /home/ubuntu/sba-backend
export GW_KEY=$(grep -E '^SUPABASE_SERVICE_KEY=' .env | sed 's/^SUPABASE_SERVICE_KEY=//' | tr -d '\r\n')
python3 - <<'EOF'
import json, urllib.request, os

KEY = os.environ["GW_KEY"]
BASE = "http://127.0.0.1:8095"

def gw(method, path, body=None):
    headers = {"apikey": KEY, "Authorization": "Bearer " + KEY, "Content-Type": "application/json"}
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read().decode()
            return r.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:200]
    except Exception as e:
        return -1, str(e)[:200]

# fetch all leads
rows = []
page = 1
while True:
    s, data = gw("GET", f"/rest/v1/leads?select=id,name,phone,legacy_id&limit=200&page={page}")
    if s != 200 or not isinstance(data, list) or not data:
        break
    rows.extend(data)
    page += 1
print("fetched:", len(rows))

# find true dup groups (same name+phone)
by_key = {}
for r in rows:
    n = (r.get("name") or "").strip().lower()
    p = (r.get("phone") or "").strip()
    if not n or not p:
        continue
    by_key.setdefault((n, p), []).append(r)

to_delete = []
backup = []
for key, members in by_key.items():
    if len(members) < 2:
        continue
    # keep the one WITH legacy_id (original import); delete the rest
    with_legacy = [m for m in members if m.get("legacy_id")]
    without = [m for m in members if not m.get("legacy_id")]
    if with_legacy and without:
        to_delete.extend(without)
    else:
        # ambiguous (e.g. two no-legacy) - keep first, delete rest
        to_delete.extend(members[1:])
    backup.extend(members)

# save backup
with open("/home/ubuntu/dup_backup_20260809.json", "w") as f:
    json.dump(backup, f, indent=2, default=str)
print("backup saved:", len(backup), "records -> /home/ubuntu/dup_backup_20260809.json")
print("to delete:", len(to_delete))

# delete
for m in to_delete:
    s, msg = gw("DELETE", f"/rest/v1/leads?id=eq.{m['id']}")
    if s != 204:
        print("  FAIL delete", m["id"], s, msg)
print("delete pass done")
EOF
'''

r = subprocess.run(
    ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-i", KEY, HOST, script2],
    capture_output=True, text=True, timeout=180,
)
print(r.stdout)
if r.stderr:
    print("STDERR:", r.stderr[:1000])
print("rc=", r.returncode)
