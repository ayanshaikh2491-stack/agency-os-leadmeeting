import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

script = r'''
PB_ADMIN="admin@tagsagency.local"; PB_PASS="pb-admin-2026-x9"
TOKEN=$(curl -s -X POST http://127.0.0.1:8090/api/collections/_superusers/auth-with-password \
  -H "Content-Type: application/json" \
  -d "{\"identity\":\"$PB_ADMIN\",\"password\":\"$PB_PASS\"}" | python3 -c "import sys,json;print(json.load(sys.stdin).get('token',''))" 2>/dev/null)

echo "=== raw PB record for Clarke Kent (legacy_id=522) ==="
curl -s -H "Authorization: $TOKEN" "http://127.0.0.1:8090/api/collections/leads__leads/records?filter=(legacy_id%3D522)" | python3 -c "
import sys, json
data = json.load(sys.stdin)
items = data.get('items', [])
print('items:', len(items))
for r in items[:2]:
    ph = r.get('phone')
    print('id:', r.get('id'))
    print('name:', repr(r.get('name')), 'type:', type(r.get('name')).__name__)
    print('phone:', repr(ph), 'type:', type(ph).__name__)
    print('legacy_id:', repr(r.get('legacy_id')))
"

echo "=== test: POST str phone into scratch collection ==="
curl -s -X POST http://127.0.0.1:8090/api/collections/scratch_phone_test/records \
  -H "Authorization: $TOKEN" -H "Content-Type: application/json" \
  -d '{"phone": "3464049915"}' | python3 -c "
import sys, json
r = json.load(sys.stdin)
print('stored phone:', repr(r.get('phone')), 'type:', type(r.get('phone')).__name__)
print('id:', r.get('id'))
"
curl -s -X DELETE "http://127.0.0.1:8090/api/collections/scratch_phone_test" -H "Authorization: $TOKEN" | head -c 100
echo
'''

r = subprocess.run(
    ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-i", KEY, HOST, script],
    capture_output=True, text=True, timeout=120,
)
print(r.stdout)
if r.stderr:
    print("STDERR:", r.stderr[:1000])
print("rc=", r.returncode)
