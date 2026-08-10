import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

script = r'''
cd /home/ubuntu/sba-backend
export GW_KEY=$(grep -E '^SUPABASE_SERVICE_KEY=' .env | sed 's/^SUPABASE_SERVICE_KEY=//' | tr -d '\r\n')
echo "=== gateway phone types now ==="
curl -s -H "apikey: $GW_KEY" -H "Authorization: Bearer $GW_KEY" -H "Content-Profile: public" \
  "http://127.0.0.1:8095/rest/v1/leads?select=id,name,phone,email&limit=1000" > /tmp/after_fix.json
python3 - <<'EOF'
import json
rows = json.load(open("/tmp/after_fix.json"))
nonstr = [r for r in rows if not isinstance(r.get("phone"), str)]
nonstr_name = [r for r in rows if not isinstance(r.get("name"), str)]
print("total:", len(rows), "| non-str phone:", len(nonstr), "| non-str name:", len(nonstr_name))
for r in rows:
    if r.get("name") == "Clarke Kent Plumbing":
        print("Clarke Kent phone:", repr(r.get("phone")), type(r.get("phone")).__name__)
    if r.get("name") == "Beyond Wow Plumbing & Drains":
        print("Beyond Wow phone:", repr(r.get("phone")), type(r.get("phone")).__name__)
EOF
echo "=== autopilot service state ==="
systemctl show sba-autopilot.service -p NRestarts -p ActiveEnterTimestamp
'''

r = subprocess.run(
    ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-i", KEY, HOST, script],
    capture_output=True, text=True, timeout=120,
)
print(r.stdout)
if r.stderr:
    print("STDERR:", r.stderr[:1000])
print("rc=", r.returncode)
