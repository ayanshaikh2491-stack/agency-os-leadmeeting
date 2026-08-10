import subprocess, os

os.chdir(r"C:\Users\TAUSHEF\Downloads\int")
KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=40):
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
                        "-o", "ConnectTimeout=8", "-i", KEY, HOST, cmd],
                       capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    print("rc=", r.returncode)
    print(r.stdout.strip()[:2500])
    if r.stderr.strip():
        print("ERR:", r.stderr.strip()[:400])
    return r

print("=== agent_persistence schema (where CEO checkpoints go) ===")
ssh("grep -n 'schema_for\\|def schema_for\\|ws_agency\\|Content-Profile' /home/ubuntu/sba-backend/admin/agency/agent_persistence.py | head -15", timeout=40)
print("=== CEO checkpointing recent writes (agent_checkpoints rows) ===")
ssh("TOKEN=$(curl -s -X POST http://127.0.0.1:8090/api/collections/_superusers/auth-with-password -H 'Content-Type: application/json' -d '{\"identity\":\"admin@tagsagency.local\",\"password\":\"pb-admin-2026-x9\"}' | python3 -c 'import sys,json; print(json.load(sys.stdin).get(\"token\",\"\"))'); curl -s -H \"Authorization: Bearer $TOKEN\" 'http://127.0.0.1:8090/api/collections/ws_agency__agent_checkpoints/records?perPage=5&sort=-created' | python3 -c 'import sys,json; d=json.load(sys.stdin); [print(r.get(\"agent_name\"), r.get(\"thread_id\",\"\")[:20], r.get(\"created\")) for r in d.get(\"items\",[])]' 2>&1 | head -8", timeout=40)
