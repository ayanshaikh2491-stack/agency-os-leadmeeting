"""Diff deployed agent_aliases.py vs local + dump backend routes."""
import os, subprocess, sys, time
sys.path.insert(0, os.getcwd())

KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def run(args, timeout=120, tries=3):
    last = None
    for i in range(tries):
        try:
            r = subprocess.run(args, capture_output=True, text=True, timeout=timeout,
                               encoding="utf-8", errors="replace")
            if r.returncode == 0 or r.stdout.strip():
                return r
            last = r
        except Exception as e:
            last = e
        time.sleep(3)
    return last

ssh = lambda cmd: run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
                       "-o", "ConnectTimeout=20", "-i", KEY, HOST, cmd])

print("== deployed agent_aliases.py head ==")
r = ssh("cd /home/ubuntu/sba-backend && sed -n '1,60p' admin/api/routes/agent_aliases.py")
print((r.stdout or "")[:3000])

print("== backend routes matching /api/agents ==")
r = ssh("cd /home/ubuntu/sba-backend && venv/bin/python - <<'PYEOF'
from admin.main import app
for route in app.routes:
    p = getattr(route, \"path\", \"\")
    if \"/api/agents\" in p:
        print(sorted(getattr(route, \"methods\", []) or []), p)
PYEOF")
print((r.stdout or "")[:3000])
if r.stderr and r.stderr.strip():
    print("STDERR:", r.stderr[-500:])

print("== gateway /api/agents/seo-engine/chat via 8095 ==")
r = ssh("curl -s -m 15 -X POST http://127.0.0.1:8095/api/agents/seo-engine/chat -H 'Content-Type: application/json' -d '{\"message\":\"hi\"}' | head -c 400")
print((r.stdout or "").strip()[:500])
