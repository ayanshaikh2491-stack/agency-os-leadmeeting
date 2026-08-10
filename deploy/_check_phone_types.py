import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

script = r'''
cd /home/ubuntu/sba-backend
export GW_KEY=$(grep -E '^SUPABASE_SERVICE_KEY=' .env | sed 's/^SUPABASE_SERVICE_KEY=//' | tr -d '\r\n')
curl -s -H "apikey: $GW_KEY" -H "Authorization: Bearer $GW_KEY" -H "Content-Profile: public" \
  "http://127.0.0.1:8095/rest/v1/leads?select=id,name,phone,email,legacy_id,created&limit=1000" > /tmp/all_leads2.json
python3 - <<'EOF'
import json
rows = json.load(open("/tmp/all_leads2.json"))
ints = [r for r in rows if isinstance(r.get("phone"), (int, float))]
strs = [r for r in rows if isinstance(r.get("phone"), str)]
print("int phone:", len(ints), " str phone:", len(strs))
print("\n-- sample STR phones (oldest 5) --")
for r in sorted(strs, key=lambda x: x.get("created") or "")[:5]:
    print("  created=%s id=%s name=%r phone=%r" % (r.get("created"), r.get("id"), r.get("name"), r.get("phone")))
print("\n-- sample INT phones (oldest 5) --")
for r in sorted(ints, key=lambda x: x.get("created") or "")[:5]:
    print("  created=%s id=%s name=%r phone=%r legacy_id=%r" % (r.get("created"), r.get("id"), r.get("name"), r.get("phone"), r.get("legacy_id")))
print("\n-- any int phones WITH legacy_id (imported)? --")
imp_ints = [r for r in ints if r.get("legacy_id")]
print("  imported int phones:", len(imp_ints), "of", len(ints))
EOF
# Also check preserved supabase export files for phone types
ls -la /home/ubuntu/pb_export/ 2>/dev/null | head -20
'''

r = subprocess.run(
    ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-i", KEY, HOST, script],
    capture_output=True, text=True, timeout=120,
)
print(r.stdout)
if r.stderr:
    print("STDERR:", r.stderr[:1000])
print("rc=", r.returncode)
