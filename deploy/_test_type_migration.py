import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

script = r'''
PB_ADMIN="admin@tagsagency.local"; PB_PASS="pb-admin-2026-x9"
TOKEN=$(curl -s -X POST http://127.0.0.1:8090/api/collections/_superusers/auth-with-password \
  -H "Content-Type: application/json" \
  -d "{\"identity\":\"$PB_ADMIN\",\"password\":\"$PB_PASS\"}" | python3 -c "import sys,json;print(json.load(sys.stdin).get('token',''))" 2>/dev/null)

# create scratch with json phone, insert int + str, then change field type to text
curl -s -X POST http://127.0.0.1:8090/api/collections \
  -H "Authorization: $TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"scratch_type_mig","type":"base","fields":[{"name":"phone","type":"json","required":false,"system":false}]}' > /dev/null
R1=$(curl -s -X POST http://127.0.0.1:8090/api/collections/scratch_type_mig/records \
  -H "Authorization: $TOKEN" -H "Content-Type: application/json" -d '{"phone": "3464049915"}' | python3 -c "import sys,json;print(json.load(sys.stdin).get('id',''))")
R2=$(curl -s -X POST http://127.0.0.1:8090/api/collections/scratch_type_mig/records \
  -H "Authorization: $TOKEN" -H "Content-Type: application/json" -d '{"phone": "+12108645223"}' | python3 -c "import sys,json;print(json.load(sys.stdin).get('id',''))")
echo "records: $R1 $R2"
echo "--- before type change ---"
curl -s -H "Authorization: $TOKEN" "http://127.0.0.1:8090/api/collections/scratch_type_mig/records?perPage=10" | python3 -c "
import sys, json
for r in json.load(sys.stdin).get('items', []):
    print('  ', r.get('id'), repr(r.get('phone')), type(r.get('phone')).__name__)
"

# change phone field json -> text
echo "--- change field to text ---"
curl -s -X PATCH http://127.0.0.1:8090/api/collections/scratch_type_mig \
  -H "Authorization: $TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"scratch_type_mig","type":"base","fields":[{"name":"phone","type":"text","required":false,"system":false,"max":0}]}' | python3 -c "import sys,json; d=json.load(sys.stdin); print('rc:', d.get('id') or d)"
echo "--- after type change ---"
curl -s -H "Authorization: $TOKEN" "http://127.0.0.1:8090/api/collections/scratch_type_mig/records?perPage=10" | python3 -c "
import sys, json
for r in json.load(sys.stdin).get('items', []):
    print('  ', r.get('id'), repr(r.get('phone')), type(r.get('phone')).__name__)
"

# now PATCH string phone
echo "--- PATCH str phone on text field ---"
curl -s -X PATCH "http://127.0.0.1:8090/api/collections/scratch_type_mig/records/$R1" \
  -H "Authorization: $TOKEN" -H "Content-Type: application/json" -d '{"phone": "512-766-0970"}' | python3 -c "
import sys, json
r = json.load(sys.stdin)
print('  patched:', repr(r.get('phone')), type(r.get('phone')).__name__)
"
# cleanup
curl -s -X DELETE "http://127.0.0.1:8090/api/collections/scratch_type_mig" -H "Authorization: $TOKEN" > /dev/null
echo cleaned
'''

r = subprocess.run(
    ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-i", KEY, HOST, script],
    capture_output=True, text=True, timeout=120,
)
print(r.stdout)
if r.stderr:
    print("STDERR:", r.stderr[:1000])
print("rc=", r.returncode)
