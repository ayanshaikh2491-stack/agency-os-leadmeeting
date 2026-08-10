import subprocess, hashlib

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

# 1. Compare deployed gateway checksum vs local
local = r"C:\Users\TAUSHEF\Downloads\int\deploy\pb_gateway.py"
with open(local, "rb") as f:
    local_hash = hashlib.sha256(f.read()).hexdigest()
print("LOCAL SHA:", local_hash)

cmds = [
    "sha256sum /home/ubuntu/sba-backend/pb_gateway.py",
    # Get gateway PID and check its cwd/env
    "ps -o pid,cmd -p 3828032 2>/dev/null || ps aux | grep pb_gateway | grep -v grep",
    # Reproduce POST with real service key from .env and capture FULL response
    "SRVKEY=$(grep -E '^SUPABASE_SERVICE_KEY=' /home/ubuntu/sba-backend/.env | sed 's/^SUPABASE_SERVICE_KEY=//' | tr -d '\\r\\n'); curl -s -X POST http://127.0.0.1:8095/rest/v1/leads -H \"apikey: $SRVKEY\" -H \"Authorization: Bearer $SRVKEY\" -H 'Content-Type: application/json' -H 'Content-Profile: leads' -d '{\"name\":\"probe-$(date +%s)\",\"phone\":\"123\"}'",
    # GET leads count via gateway
    "SRVKEY=$(grep -E '^SUPABASE_SERVICE_KEY=' /home/ubuntu/sba-backend/.env | sed 's/^SUPABASE_SERVICE_KEY=//' | tr -d '\\r\\n'); curl -s -X GET 'http://127.0.0.1:8095/rest/v1/leads?select=count' -H \"apikey: $SRVKEY\" -H 'Authorization: Bearer $SRVKEY' | head -c 300",
    # Direct PocketBase collection list to see what exists
    "TOKEN=$(curl -s -X POST http://127.0.0.1:8090/api/collections/_superusers/auth-with-password -H 'Content-Type: application/json' -d '{\"identity\":\"admin@tagsagency.local\",\"password\":\"pb-admin-2026-x9\"}' | python3 -c 'import sys,json; print(json.load(sys.stdin).get(\"token\",\"\"))' 2>/dev/null); curl -s http://127.0.0.1:8090/api/collections?perPage=100 -H \"Authorization: Bearer $TOKEN\" | python3 -c 'import sys,json; d=json.load(sys.stdin); print([i[\"name\"] for i in d.get(\"items\",[])])' 2>/dev/null | head -c 1000",
]

for cmd in cmds:
    print("=" * 20)
    print("CMD:", cmd[:100])
    try:
        r = subprocess.run(
            ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
             "-o", "ConnectTimeout=10", "-i", KEY, HOST, cmd],
            capture_output=True, text=True, timeout=40, encoding="utf-8", errors="replace",
        )
        print("RC:", r.returncode)
        print("OUT:", r.stdout.strip()[:2500])
        print("ERR:", r.stderr.strip()[:500])
    except Exception as e:
        print("EXC:", e)
