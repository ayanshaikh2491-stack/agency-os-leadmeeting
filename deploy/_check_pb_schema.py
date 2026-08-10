import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

script = r'''
# Check PB collection schema for leads
PB_ADMIN=$(grep -E '^PB_ADMIN_EMAIL=' /home/ubuntu/pocketbase/.env 2>/dev/null | cut -d= -f2)
PB_PASS=$(grep -E '^PB_ADMIN_PASS=' /home/ubuntu/pocketbase/.env 2>/dev/null | cut -d= -f2)
if [ -z "$PB_ADMIN" ]; then PB_ADMIN="admin@tagsagency.local"; PB_PASS="pb-admin-2026-x9"; fi
TOKEN=$(curl -s -X POST http://127.0.0.1:8090/api/collections/_superusers/auth-with-password \
  -H "Content-Type: application/json" \
  -d "{\"identity\":\"$PB_ADMIN\",\"password\":\"$PB_PASS\"}" | python3 -c "import sys,json;print(json.load(sys.stdin).get('token',''))" 2>/dev/null)
echo "token len: ${#TOKEN}"
curl -s -H "Authorization: $TOKEN" http://127.0.0.1:8090/api/collections/leads__leads | python3 -c "
import sys, json
c = json.load(sys.stdin)
print('name:', c.get('name'))
print('type:', c.get('type'))
for f in c.get('fields', []):
    print('  field:', f.get('name'), '| type:', f.get('type'), '| required:', f.get('required'))
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
