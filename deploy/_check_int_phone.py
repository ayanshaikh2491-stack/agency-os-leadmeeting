import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

script = r'''
cd /home/ubuntu/sba-backend
export GW_KEY=$(grep -E '^SUPABASE_SERVICE_KEY=' .env | sed 's/^SUPABASE_SERVICE_KEY=//' | tr -d '\r\n')
curl -s -H "apikey: $GW_KEY" -H "Authorization: Bearer $GW_KEY" -H "Content-Profile: public" \
  "http://127.0.0.1:8095/rest/v1/leads?select=id,name,phone,email&limit=1000" > /tmp/all_leads.json
python3 - <<'EOF'
import json
rows = json.load(open("/tmp/all_leads.json"))
ints = [r for r in rows if isinstance(r.get("phone"), int) or isinstance(r.get("phone"), float)]
print("total leads:", len(rows))
print("non-str phone count:", len(ints))
for r in ints[:15]:
    print("  id=%s name=%r phone=%r type=%s" % (r.get("id"), r.get("name"), r.get("phone"), type(r.get("phone")).__name__))
# also non-str names/websites
bad_name = [r for r in rows if not isinstance(r.get("name"), str)]
bad_web = [r for r in rows if not isinstance(r.get("website"), str) and r.get("website") is not None]
print("non-str name count:", len(bad_name))
print("non-str website count:", len(bad_web))
for r in bad_web[:10]:
    print("  web id=%s name=%r website=%r type=%s" % (r.get("id"), r.get("name"), r.get("website"), type(r.get("website")).__name__))
EOF
'''

r = subprocess.run(
    ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-i", KEY, HOST, script],
    capture_output=True, text=True, timeout=120,
)
print(r.stdout)
if r.stderr:
    print("STDERR:", r.stderr[:1000])
print("rc=", r.returncode)
