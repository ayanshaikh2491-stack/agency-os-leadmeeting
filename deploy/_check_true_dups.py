import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

script = r'''
cd /home/ubuntu/sba-backend
export GW_KEY=$(grep -E '^SUPABASE_SERVICE_KEY=' .env | sed 's/^SUPABASE_SERVICE_KEY=//' | tr -d '\r\n')
curl -s -H "apikey: $GW_KEY" -H "Authorization: Bearer $GW_KEY" -H "Content-Profile: public" \
  "http://127.0.0.1:8095/rest/v1/leads?select=id,name,phone,email,legacy_id,created_at&limit=1000" > /tmp/all4.json
python3 - <<'EOF'
import json
rows = json.load(open("/tmp/all4.json"))
# true dup = same (name.lower, phone) with DIFFERENT pb ids
by_key = {}
for r in rows:
    n = (r.get("name") or "").lower().strip()
    p = (r.get("phone") or "").strip()
    if not n or not p:
        continue
    by_key.setdefault((n, p), []).append(r)
true_dups = {k: v for k, v in by_key.items() if len(v) > 1}
print("TRUE duplicate groups (same name+phone):", len(true_dups))
total_extra = sum(len(v) - 1 for v in true_dups.values())
print("extra duplicate records:", total_extra)
for k, v in list(true_dups.items())[:12]:
    print("  ", k, "->", [(r.get("id"), r.get("legacy_id"), r.get("created_at")) for r in v])
EOF
echo "=== autopilot latest journal ==="
sudo journalctl -u sba-autopilot.service --since '2026-08-09 16:44:30' --no-pager | tail -25
'''

r = subprocess.run(
    ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-i", KEY, HOST, script],
    capture_output=True, text=True, timeout=120,
)
print(r.stdout)
if r.stderr:
    print("STDERR:", r.stderr[:1000])
print("rc=", r.returncode)
