"""EC2 diagnostics: services, PB collections, memory agent files."""
import os, subprocess, sys, time
sys.path.insert(0, os.getcwd())

KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=90, tries=2):
    last = None
    for i in range(tries):
        try:
            r = subprocess.run(
                ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
                 "-o", "ConnectTimeout=20", "-i", KEY, HOST, cmd],
                capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
            if r.returncode == 0 or r.stdout.strip():
                return r
            last = r
        except Exception as e:
            last = e
        time.sleep(3)
    return last

def show(title, cmd):
    print(f"\n===== {title} =====")
    r = ssh(cmd)
    if isinstance(r, subprocess.CompletedProcess):
        print((r.stdout or "").strip()[:2000] or "(no output) rc=%s" % r.returncode)
        if r.stderr and r.stderr.strip():
            print("STDERR:", r.stderr.strip()[:300])
    else:
        print("SSH FAILED:", r)

show("Services", "systemctl is-active sba sba-autopilot sba-gateway sba-chrome pocketbase 2>&1; echo '---'; systemctl --type=service --no-legend | grep -iE 'sba|pocketbase|gateway'")

show("PB collections via gateway", r'''cd /home/ubuntu/sba-backend && GW_KEY=$(grep -E '^SUPABASE_SERVICE_KEY=' .env | sed 's/^SUPABASE_SERVICE_KEY=//' | tr -d '\r\n') && curl -s -m 15 -H "apikey: $GW_KEY" -H "Authorization: Bearer $GW_KEY" "http://127.0.0.1:8095/rest/v1/?apikey=$GW_KEY" 2>/dev/null | head -c 300; echo; curl -s -m 15 "http://127.0.0.1:8095/health" 2>/dev/null | head -c 200''')

show("PB data dir collections", "ls /home/ubuntu/pocketbase/pb_data 2>/dev/null | head -30; echo '---'; ls /home/ubuntu/pocketbase/pb_data/storage 2>/dev/null | head -20")

show("Memory agent file", "ls -la /home/ubuntu/sba-backend/admin/workspace/agents/ 2>/dev/null; echo '---'; ls /home/ubuntu/sba-backend/admin/agency/ 2>/dev/null | grep -iE 'mem|persist|agent_persist'")

show("Memory/agent persistence module", "grep -rn 'class.*Memory\\|def.*memory\\|MemorySaver\\|agent_persistence' /home/ubuntu/sba-backend/admin/agency/agent_persistence.py 2>/dev/null | head -20")

show("SBA frontend error check - backend chat", "curl -s -m 20 -X POST http://127.0.0.1:8000/api/sba/chat -H 'Content-Type: application/json' -d '{\"message\":\"hi\",\"session_id\":\"probe\"}' | head -c 400")
