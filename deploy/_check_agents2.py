import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

script = r'''
echo "=== backend on 8000? ==="
curl -s -m 5 http://127.0.0.1:8000/api/health | python3 -m json.tool 2>/dev/null || echo "8000 fail"
echo "=== backend on 8050? ==="
curl -s -m 5 http://127.0.0.1:8050/api/health | python3 -m json.tool 2>/dev/null || echo "8050 fail"
echo "=== listening ports ==="
ss -tlnp 2>/dev/null | grep -E '8000|8050|8090|8095' || netstat -tlnp 2>/dev/null | grep -E '8000|8050|8090|8095'
echo "=== agents in PB (via gateway) ==="
cd /home/ubuntu/sba-backend
export GW_KEY=$(grep -E '^SUPABASE_SERVICE_KEY=' .env | sed 's/^SUPABASE_SERVICE_KEY=//' | tr -d '\r\n')
curl -s -m 10 -H "apikey: $GW_KEY" -H "Authorization: Bearer $GW_KEY" \
  "http://127.0.0.1:8095/rest/v1/agents?select=name,status,enabled&limit=50" | python3 -m json.tool 2>/dev/null | head -60
echo "=== agent names only ==="
curl -s -m 10 -H "apikey: $GW_KEY" -H "Authorization: Bearer $GW_KEY" \
  "http://127.0.0.1:8095/rest/v1/agents?select=name&limit=50" | python3 -c "import sys,json; [print(' -', r.get('name')) for r in json.load(sys.stdin)]" 2>/dev/null
'''

r = subprocess.run(
    ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-i", KEY, HOST, script],
    capture_output=True, text=True, timeout=120,
)
print(r.stdout)
if r.stderr:
    print("STDERR:", r.stderr[:1000])
print("rc=", r.returncode)
