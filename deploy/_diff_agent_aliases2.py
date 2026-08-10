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
scp = lambda src, dst: run(["scp", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
                            "-i", KEY, src, f"{HOST}:{dst}"])

print("== deployed agent_aliases.py AGENT_SLUG_MAP ==")
r = ssh("cd /home/ubuntu/sba-backend && grep -n 'AGENT_SLUG_MAP' -A 10 admin/api/routes/agent_aliases.py | head -15")
print((r.stdout or "")[:1200])

print("== deployed file local diff (md5) ==")
r = ssh("md5sum admin/api/routes/agent_aliases.py")
print((r.stdout or "").strip())
import hashlib
with open(os.path.join(os.getcwd(), "admin", "api", "routes", "agent_aliases.py"), "rb") as f:
    print("local:", hashlib.md5(f.read()).hexdigest())

print("== dump routes ==")
r = scp(os.path.join(os.getcwd(), "deploy", "_dump_routes.py"), "/home/ubuntu/sba-backend/_dump_routes.py")
r = ssh("cd /home/ubuntu/sba-backend && venv/bin/python _dump_routes.py 2>&1 | head -40")
print((r.stdout or "")[:3000])
if r.stderr and r.stderr.strip():
    print("STDERR:", r.stderr[-500:])

print("== gateway seo-engine chat ==")
r = ssh("curl -s -m 15 -X POST http://127.0.0.1:8095/api/agents/seo-engine/chat -H 'Content-Type: application/json' -d '{\"message\":\"hi\"}' | head -c 400")
print((r.stdout or "").strip()[:500])
