import subprocess, os, json

os.chdir(r"C:\Users\TAUSHEF\Downloads\int")
KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=60):
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
                        "-o", "ConnectTimeout=10", "-i", KEY, HOST, cmd],
                       capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    print(r.stdout.strip()[:3500])
    if r.stderr.strip():
        print("ERR:", r.stderr.strip()[:400])
    return r

# 1. Get SERVICE_KEY from backend .env (masked output)
r = ssh("grep -E 'SUPABASE_URL|SUPABASE_SERVICE_KEY|SERVICE_KEY' /home/ubuntu/sba-backend/.env | sed -E 's/(KEY=).{6}.*/\\1***masked***/'")
# 2. Proper PB admin auth -> list collections
print("=== PB collections via admin auth ===")
r = ssh("TOKEN=$(curl -s -X POST http://127.0.0.1:8090/api/collections/_superusers/auth-with-password -H 'Content-Type: application/json' -d '{\"identity\":\"admin@tagsagency.local\",\"password\":\"pb-admin-2026-x9\"}' | python3 -c 'import sys,json; print(json.load(sys.stdin).get(\"token\",\"\"))'); echo \"token_len=${#TOKEN}\"; curl -s -H \"Authorization: Bearer $TOKEN\" 'http://127.0.0.1:8090/api/collections?perPage=200' | python3 -c 'import sys,json; d=json.load(sys.stdin); items=d.get(\"items\",[]); print(\"collections:\",len(items)); [print(\"-\",c[\"name\"]) for c in items]' 2>&1 | head -40", timeout=45)
