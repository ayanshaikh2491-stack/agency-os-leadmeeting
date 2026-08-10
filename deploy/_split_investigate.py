import subprocess, os

os.chdir(r"C:\Users\TAUSHEF\Downloads\int")
KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=60):
    print(">>>", cmd)
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
                        "-o", "ConnectTimeout=10", "-i", KEY, HOST, cmd],
                       capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    print("rc=", r.returncode)
    print(r.stdout.strip()[:3000])
    if r.stderr.strip():
        print("ERR:", r.stderr.strip()[:400])
    return r

print("=== backend Content-Profile usage ===")
ssh("grep -rn 'Content-Profile\\|content-profile\\|content_profile' /home/ubuntu/sba-backend --include='*.py' | head -15", timeout=45)
print("=== what are the 2 leads__leads records ===")
ssh("TOKEN=$(curl -s -X POST http://127.0.0.1:8090/api/collections/_superusers/auth-with-password -H 'Content-Type: application/json' -d '{\"identity\":\"admin@tagsagency.local\",\"password\":\"pb-admin-2026-x9\"}' | python3 -c 'import sys,json; print(json.load(sys.stdin).get(\"token\",\"\"))'); curl -s -H \"Authorization: Bearer $TOKEN\" 'http://127.0.0.1:8090/api/collections/leads__leads/records?perPage=10' | python3 -m json.tool | head -50", timeout=45)
print("=== autopilot no_email logic ===")
ssh("grep -n 'no_email\\|no-email\\|no email' /home/ubuntu/sba-backend/admin/agency/sba_autopilot.py | head -20", timeout=45)
