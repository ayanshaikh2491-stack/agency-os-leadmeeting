import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

script = r'''
PB_ADMIN="admin@tagsagency.local"; PB_PASS="pb-admin-2026-x9"
TOKEN=$(curl -s -X POST http://127.0.0.1:8090/api/collections/_superusers/auth-with-password \
  -H "Content-Type: application/json" \
  -d "{\"identity\":\"$PB_ADMIN\",\"password\":\"$PB_PASS\"}" | python3 -c "import sys,json;print(json.load(sys.stdin).get('token',''))" 2>/dev/null)

echo "=== leads__leads count after dedup ==="
curl -s -H "Authorization: $TOKEN" "http://127.0.0.1:8090/api/collections/leads__leads/records?perPage=1" | python3 -c "import sys,json; d=json.load(sys.stdin); print('totalItems:', d.get('totalItems'))"

echo "=== ws_agency__leads phone types ==="
curl -s -H "Authorization: $TOKEN" "http://127.0.0.1:8090/api/collections/ws_agency__leads/records?perPage=200&page=1" > /tmp/ws_p1.json
python3 - <<'EOF'
import json
d = json.load(open("/tmp/ws_p1.json"))
items = d.get("items", [])
print("ws_agency__leads totalItems:", d.get("totalItems"), "fetched:", len(items))
ints = [r for r in items if isinstance(r.get("phone"), (int, float))]
print("int phone:", len(ints))
for r in ints[:5]:
    print("  ", r.get("id"), r.get("name"), repr(r.get("phone")), r.get("legacy_id"))
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
