import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

cmds = [
    # Reproduce the import-style POST: body carries Supabase UUID id
    "SRVKEY=$(grep -E '^SUPABASE_SERVICE_KEY=' /home/ubuntu/sba-backend/.env | sed 's/^SUPABASE_SERVICE_KEY=//' | tr -d '\\r\\n'); curl -s -X POST http://127.0.0.1:8095/rest/v1/leads -H \"apikey: $SRVKEY\" -H 'Authorization: Bearer $SRVKEY' -H 'Content-Type: application/json' -H 'Content-Profile: leads' -d '{\"id\":\"b0f3c1e2-0000-4000-8000-000000000001\",\"name\":\"id-test\",\"phone\":\"555\"}'",
    # Integer id variant
    "SRVKEY=$(grep -E '^SUPABASE_SERVICE_KEY=' /home/ubuntu/sba-backend/.env | sed 's/^SUPABASE_SERVICE_KEY=//' | tr -d '\\r\\n'); curl -s -X POST http://127.0.0.1:8095/rest/v1/leads -H \"apikey: $SRVKEY\" -H 'Authorization: Bearer $SRVKEY' -H 'Content-Type: application/json' -H 'Content-Profile: leads' -d '{\"id\":42,\"name\":\"id-int-test\",\"phone\":\"555\"}'",
    # GET by id=eq filter works?
    "SRVKEY=$(grep -E '^SUPABASE_SERVICE_KEY=' /home/ubuntu/sba-backend/.env | sed 's/^SUPABASE_SERVICE_KEY=//' | tr -d '\\r\\n'); curl -s 'http://127.0.0.1:8095/rest/v1/leads?name=eq.id-test' -H \"apikey: $SRVKEY\" -H 'Authorization: Bearer $SRVKEY' | head -c 600",
]

for cmd in cmds:
    print("=" * 20)
    print("CMD:", cmd[:120])
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
