import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

script = r'''
PB_ADMIN="admin@tagsagency.local"; PB_PASS="pb-admin-2026-x9"
TOKEN=$(curl -s -X POST http://127.0.0.1:8090/api/collections/_superusers/auth-with-password \
  -H "Content-Type: application/json" \
  -d "{\"identity\":\"$PB_ADMIN\",\"password\":\"$PB_PASS\"}" | python3 -c "import sys,json;print(json.load(sys.stdin).get('token',''))" 2>/dev/null)

echo "=== collection leads (NO prefix) ==="
curl -s -H "Authorization: $TOKEN" "http://127.0.0.1:8090/api/collections/leads/records?perPage=3" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('totalItems:', d.get('totalItems'))
for r in d.get('items', [])[:3]:
    print('  ', r.get('id'), repr(r.get('name')), repr(r.get('phone')), 'legacy:', r.get('legacy_id'))
"

echo "=== all collections list ==="
curl -s -H "Authorization: $TOKEN" "http://127.0.0.1:8090/api/collections?perPage=100" | python3 -c "
import sys, json
d = json.load(sys.stdin)
for c in d.get('items', []):
    print('  ', c.get('name'), '| totalItems via count:', end=' ')
EOF
" 2>/dev/null || echo "(listing needs different call)"
curl -s -H "Authorization: $TOKEN" "http://127.0.0.1:8090/api/collections?perPage=100" | python3 -c "
import sys, json
d = json.load(sys.stdin)
for c in d.get('items', []):
    print('  ', c.get('name'))
"
'''

r = subprocess.run(
    ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-i", KEY, HOST, script],
    capture_output=True, text=True, timeout=120,
)
print(r.stdout)
if r.stderr:
    print("STDERR:", r.stderr[:1000])
print("rc=", r.returncode)
