import subprocess, os

os.chdir(r"C:\Users\TAUSHEF\Downloads\int")
KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=90):
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
                        "-o", "ConnectTimeout=10", "-i", KEY, HOST, cmd],
                       capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    print("rc=", r.returncode)
    print(r.stdout.strip()[:2500])
    if r.stderr.strip():
        print("ERR:", r.stderr.strip()[:500])
    return r

# 1. Verify id-sanitize on EC2 (UUID id POST -> must not 500, legacy_id remap)
ssh("SRVKEY=$(grep -E '^SUPABASE_SERVICE_KEY=' /home/ubuntu/sba-backend/.env | sed 's/^SUPABASE_SERVICE_KEY=//' | tr -d '\\r\\n\"; echo \"KEY=${SRVKEY:0:20}...\"; curl -s -X POST http://127.0.0.1:8095/rest/v1/leads -H \"apikey: $SRVKEY\" -H 'Authorization: Bearer $SRVKEY' -H 'Content-Type: application/json' -H 'Content-Profile: leads' -d '{\"id\":\"b0f3c1e2-0000-4000-8000-000000000099\",\"name\":\"ec2-id-test\",\"phone\":\"777\"}'")

# 2. Point backend .env at gateway
ssh("grep -n 'SUPABASE_URL' /home/ubuntu/sba-backend/.env; sed -i 's|^SUPABASE_URL=.*|SUPABASE_URL=http://127.0.0.1:8095|' /home/ubuntu/sba-backend/.env; grep -n 'SUPABASE_URL' /home/ubuntu/sba-backend/.env")

# 3. Restart backend
ssh("sudo systemctl restart sba.service; sleep 6; sudo systemctl is-active sba.service")
