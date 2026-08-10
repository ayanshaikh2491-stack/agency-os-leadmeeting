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
    print(r.stdout.strip()[:3500])
    if r.stderr.strip():
        print("ERR:", r.stderr.strip()[:400])
    return r

print("=== autopilot pass summaries since 14:00 (email sends) ===")
ssh("journalctl -u sba-autopilot.service --since '14:00' --no-pager | grep -E 'pass|summary|emails_sent|send_failed|no_email|deferred|550|SMTP|reply|meeting' | tail -30", timeout=45)
print("=== gateway/PB collections (new auto-created ones?) ===")
ssh("curl -s -H 'Authorization: Bearer pb-admin-2026-x9' http://127.0.0.1:8090/api/collections?perPage=100 | python3 -c \"import sys,json; d=json.load(sys.stdin); print('collections:', len(d.get('items',[]))); [print('-', c['name']) for c in d.get('items',[])]\" 2>/dev/null || curl -s http://127.0.0.1:8090/api/health", timeout=45)
print("=== backend agent_memory / CEO checkpoint table via gateway ===")
ssh("curl -s 'http://127.0.0.1:8095/rest/v1/agent_memory?select=*&limit=5' -H 'apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.placeholder' -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.placeholder' | head -c 400; echo", timeout=45)
