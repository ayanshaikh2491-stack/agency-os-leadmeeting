import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

script = r'''
cd /home/ubuntu/sba-backend
ls -la _pb_import.py deploy/_pb_import.py 2>/dev/null
export GW_KEY=$(grep -E '^SUPABASE_SERVICE_KEY=' .env | sed 's/^SUPABASE_SERVICE_KEY=//' | tr -d '\r\n')
echo "GW_KEY len: ${#GW_KEY}"
# run importer (idempotent: skips legacy_ids already present; probes have no legacy_id so no collision)
if [ -f _pb_import.py ]; then
  venv/bin/python _pb_import.py /home/ubuntu/pb_export http://127.0.0.1:8095 "$GW_KEY"
elif [ -f deploy/_pb_import.py ]; then
  venv/bin/python deploy/_pb_import.py /home/ubuntu/pb_export http://127.0.0.1:8095 "$GW_KEY"
else
  echo "IMPORTER NOT FOUND"
fi
'''

r = subprocess.run(
    ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-i", KEY, HOST, script],
    capture_output=True, text=True, timeout=600,
)
print(r.stdout)
if r.stderr:
    print("STDERR:", r.stderr[:2000])
print("rc=", r.returncode)
