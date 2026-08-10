import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

script = r'''
PB_ADMIN="admin@tagsagency.local"; PB_PASS="pb-admin-2026-x9"
TOKEN=$(curl -s -X POST http://127.0.0.1:8090/api/collections/_superusers/auth-with-password \
  -H "Content-Type: application/json" \
  -d "{\"identity\":\"$PB_ADMIN\",\"password\":\"$PB_PASS\"}" | python3 -c "import sys,json;print(json.load(sys.stdin).get('token',''))" 2>/dev/null)

echo "=== ALL leads__leads records (direct PB) ==="
curl -s -H "Authorization: $TOKEN" "http://127.0.0.1:8090/api/collections/leads__leads/records?perPage=10" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('totalItems:', d.get('totalItems'))
for r in d.get('items', []):
    print('  ', r.get('id'), repr(r.get('name')), repr(r.get('phone')), 'legacy:', r.get('legacy_id'))
"

echo "=== gateway count ==="
cd /home/ubuntu/sba-backend
export GW_KEY=$(grep -E '^SUPABASE_SERVICE_KEY=' .env | sed 's/^SUPABASE_SERVICE_KEY=//' | tr -d '\r\n')
curl -s -H "apikey: $GW_KEY" -H "Authorization: Bearer $GW_KEY" -H "Content-Profile: public" \
  "http://127.0.0.1:8095/rest/v1/leads?select=id&limit=5" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('gateway returns:', len(d) if isinstance(d, list) else d)
"
echo "=== export file intact? ==="
wc -l /home/ubuntu/pb_export/public__leads.jsonl
'''

r = subprocess.run(
    ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-i", KEY, HOST, script],
    capture_output=True, text=True, timeout=120,
)
print(r.stdout)
if r.stderr:
    print("STDERR:", r.stderr[:1000])
print("rc=", r.returncode)
