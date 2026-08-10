import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

script = r'''
PB_ADMIN="admin@tagsagency.local"; PB_PASS="pb-admin-2026-x9"
TOKEN=$(curl -s -X POST http://127.0.0.1:8090/api/collections/_superusers/auth-with-password \
  -H "Content-Type: application/json" \
  -d "{\"identity\":\"$PB_ADMIN\",\"password\":\"$PB_PASS\"}" | python3 -c "import sys,json;print(json.load(sys.stdin).get('token',''))" 2>/dev/null)
echo "=== leads collection schema (phone/name/email/website fields only) ==="
curl -s -H "Authorization: $TOKEN" "http://127.0.0.1:8090/api/collections/leads" | python3 -c "
import sys, json
c = json.load(sys.stdin)
for f in c.get('fields', []):
    if f.get('name') in ('id','name','phone','email','website','status','category','city_state','has_website','legacy_id','workspace_name','email_provenance','created_at','updated_at'):
        print('  ', f.get('name'), '|', f.get('type'))
"
echo "=== non-legacy leads in collection leads ==="
curl -s -H "Authorization: $TOKEN" "http://127.0.0.1:8090/api/collections/leads/records?perPage=200&page=1" > /tmp/leads_p1.json
curl -s -H "Authorization: $TOKEN" "http://127.0.0.1:8090/api/collections/leads/records?perPage=200&page=2" > /tmp/leads_p2.json
curl -s -H "Authorization: $TOKEN" "http://127.0.0.1:8090/api/collections/leads/records?perPage=200&page=3" > /tmp/leads_p3.json
curl -s -H "Authorization: $TOKEN" "http://127.0.0.1:8090/api/collections/leads/records?perPage=200&page=4" > /tmp/leads_p4.json
curl -s -H "Authorization: $TOKEN" "http://127.0.0.1:8090/api/collections/leads/records?perPage=200&page=5" > /tmp/leads_p5.json
python3 - <<'EOF'
import json
items = []
for i in range(1, 6):
    try:
        d = json.load(open(f"/tmp/leads_p{i}.json"))
        items.extend(d.get("items", []))
    except Exception as e:
        print("page", i, "err", e)
print("fetched:", len(items))
nonleg = [r for r in items if not r.get("legacy_id")]
print("non-legacy:", len(nonleg))
for r in nonleg:
    print("  ", r.get("id"), repr(r.get("name")), repr(r.get("phone")))
ints = [r for r in items if isinstance(r.get("phone"), (int, float))]
print("int phone at rest:", len(ints))
EOF
'''

r = subprocess.run(
    ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-i", KEY, HOST, script],
    capture_output=True, text=True, timeout=120,
)
print(r.stdout)
if r.stderr:
    print("STDERR:", r.stderr[:1000])
print("rc=", r.returncode)
