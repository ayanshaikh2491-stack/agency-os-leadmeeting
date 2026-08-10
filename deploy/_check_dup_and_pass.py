import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

script = r'''
cd /home/ubuntu/sba-backend
export GW_KEY=$(grep -E '^SUPABASE_SERVICE_KEY=' .env | sed 's/^SUPABASE_SERVICE_KEY=//' | tr -d '\r\n')
echo "=== non-str name lead ==="
curl -s -H "apikey: $GW_KEY" -H "Authorization: Bearer $GW_KEY" -H "Content-Profile: public" \
  "http://127.0.0.1:8095/rest/v1/leads?select=id,name,phone,email,legacy_id&limit=1000" > /tmp/all3.json
python3 - <<'EOF'
import json
rows = json.load(open("/tmp/all3.json"))
for r in rows:
    if not isinstance(r.get("name"), str):
        print("NON-STR NAME:", r.get("id"), repr(r.get("name")), type(r.get("name")).__name__, "legacy_id:", r.get("legacy_id"))
names = {}
for r in rows:
    n = (r.get("name") or "").lower().strip()
    names.setdefault(n, []).append((r.get("id"), r.get("phone"), r.get("legacy_id")))
dups = {n: v for n, v in names.items() if len(v) > 1}
print("duplicate-name groups:", len(dups))
for n, v in list(dups.items())[:8]:
    print("  ", repr(n), v)
EOF
echo "=== autopilot pass since restart ==="
sudo journalctl -u sba-autopilot.service --since '2026-08-09 16:44:00' --no-pager | grep -E 'autopilot pass|lead finding|lead rotation|WARNING|ERROR|Traceback' | tail -12
'''

r = subprocess.run(
    ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-i", KEY, HOST, script],
    capture_output=True, text=True, timeout=120,
)
print(r.stdout)
if r.stderr:
    print("STDERR:", r.stderr[:1000])
print("rc=", r.returncode)
