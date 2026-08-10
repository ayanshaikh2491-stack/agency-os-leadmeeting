"""Check /api/sba/* endpoints + frontend build on Vercel."""
import os, subprocess, sys, time, json, urllib.request
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

# Dump all /api/sba routes registered in the backend
r = ssh("cd /home/ubuntu/sba-backend && venv/bin/python -c 'import os,sys; sys.path.insert(0,\"/home/ubuntu/sba-backend\"); from admin.main import app; [print(sorted(getattr(r,\"methods\",[]) or []), getattr(r,\"path\",\"\")) for r in app.routes if \"/api/sba\" in getattr(r,\"path\",\"\") or \"/api/agents\" in getattr(r,\"path\",\"\")]' 2>&1 | head -60")
print("== backend /api/sba + /api/agents routes ==")
print((r.stdout or "")[:4000])
if r.stderr and r.stderr.strip():
    print("STDERR:", r.stderr[-600:])
