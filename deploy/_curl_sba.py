"""Curl /api/sba/* and /api/agents/* endpoints on EC2 port 8000."""
import os, subprocess, sys, time
sys.path.insert(0, os.getcwd())

KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def run(args, timeout=90, tries=3):
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

cmds = [
    ("GET /api/sba/agents", "curl -s -m 15 -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/api/sba/agents"),
    ("GET /api/sba/platforms", "curl -s -m 15 -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/api/sba/platforms"),
    ("GET /api/sba/status", "curl -s -m 15 http://127.0.0.1:8000/api/sba/status | head -c 300"),
    ("GET /api/sba/pipeline", "curl -s -m 15 http://127.0.0.1:8000/api/sba/pipeline | head -c 200"),
    ("GET /api/sba/meetings", "curl -s -m 15 http://127.0.0.1:8000/api/sba/meetings | head -c 200"),
    ("GET /api/sba/finance", "curl -s -m 15 http://127.0.0.1:8000/api/sba/finance | head -c 200"),
    ("POST /api/sba/chat", "curl -s -m 30 -X POST http://127.0.0.1:8000/api/sba/chat -H 'Content-Type: application/json' -d '{\"message\":\"hi\"}' | head -c 200"),
]
for title, cmd in cmds:
    r = ssh(cmd)
    out = (r.stdout or "").strip() if isinstance(r, subprocess.CompletedProcess) else str(r)
    print(f"{title}: {out[:400]}")
