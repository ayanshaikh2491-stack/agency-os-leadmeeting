import subprocess, os

os.chdir(r"C:\Users\TAUSHEF\Downloads\int")
KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=60):
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
                        "-o", "ConnectTimeout=8", "-i", KEY, HOST, cmd],
                       capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    print("rc=", r.returncode)
    print(r.stdout.strip()[:3500])
    if r.stderr.strip():
        print("ERR:", r.stderr.strip()[:400])
    return r

# Get the real service key without echoing it fully
print("=== fetch leads exactly like backend, count rows ===")
ssh("SKEY=$(grep '^SUPABASE_SERVICE_KEY=' /home/ubuntu/sba-backend/.env | cut -d= -f2 | tr -d '\"'); curl -s -m 60 'http://127.0.0.1:8095/rest/v1/leads?select=*&order=created_at.asc' -H \"apikey: $SKEY\" -H \"Authorization: Bearer $SKEY\" -o /tmp/all_leads.json; python3 -c \"import json; d=json.load(open('/tmp/all_leads.json')); print('rows returned:', len(d)); ws={}; ne=0; tot=len(d);\nfor r in d:\n    ws[r.get('workspace_name') or '(none)']=ws.get(r.get('workspace_name') or '(none)',0)+1\n    if not (r.get('email') or '').strip(): ne+=1\nprint('no_email rows:', ne)\nprint('workspace dist:', ws)\"", timeout=90)
