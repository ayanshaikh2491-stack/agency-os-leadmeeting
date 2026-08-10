import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

script = r'''
PB_ADMIN="admin@tagsagency.local"; PB_PASS="pb-admin-2026-x9"
TOKEN=$(curl -s -X POST http://127.0.0.1:8090/api/collections/_superusers/auth-with-password \
  -H "Content-Type: application/json" \
  -d "{\"identity\":\"$PB_ADMIN\",\"password\":\"$PB_PASS\"}" | python3 -c "import sys,json;print(json.load(sys.stdin).get('token',''))" 2>/dev/null)

echo "=== raw PB record Clarke Kent by id ==="
curl -s -H "Authorization: $TOKEN" "http://127.0.0.1:8090/api/collections/leads__leads/records/9bk8fc2l8uitd7h" | python3 -c "
import sys, json
r = json.load(sys.stdin)
print('name:', repr(r.get('name')), type(r.get('name')).__name__)
print('phone:', repr(r.get('phone')), type(r.get('phone')).__name__)
print('legacy_id:', repr(r.get('legacy_id')))
print('created:', r.get('created'))
"

echo "=== create scratch collection + test str phone ==="
curl -s -X POST http://127.0.0.1:8090/api/collections \
  -H "Authorization: $TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"scratch_phone_test","type":"base","fields":[{"name":"phone","type":"json","required":false,"system":false}]}' | python3 -c "import sys,json; print('create rc:', json.load(sys.stdin).get('id') or json.load(sys.stdin))"
RID=$(curl -s -X POST http://127.0.0.1:8090/api/collections/scratch_phone_test/records \
  -H "Authorization: $TOKEN" -H "Content-Type: application/json" \
  -d '{"phone": "3464049915"}' | python3 -c "import sys,json; r=json.load(sys.stdin); print(r.get('id',''))")
echo "created record id: $RID"
curl -s -H "Authorization: $TOKEN" "http://127.0.0.1:8090/api/collections/scratch_phone_test/records/$RID" | python3 -c "
import sys, json
r = json.load(sys.stdin)
print('stored phone:', repr(r.get('phone')), 'type:', type(r.get('phone')).__name__)
"
# cleanup
curl -s -X DELETE "http://127.0.0.1:8090/api/collections/scratch_phone_test" -H "Authorization: $TOKEN" > /dev/null
echo "cleaned"
'''

r = subprocess.run(
    ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-i", KEY, HOST, script],
    capture_output=True, text=True, timeout=120,
)
print(r.stdout)
if r.stderr:
    print("STDERR:", r.stderr[:1000])
print("rc=", r.returncode)
