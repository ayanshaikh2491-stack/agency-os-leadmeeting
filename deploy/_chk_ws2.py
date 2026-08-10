"""Retry workspace config + DB source check with aggressive retries."""
import os, subprocess, sys, time, json
sys.path.insert(0, os.getcwd())

KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=90, tries=5):
    last = None
    for i in range(tries):
        try:
            r = subprocess.run(
                ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
                 "-o", "ConnectTimeout=15", "-o", "ServerAliveInterval=10",
                 "-i", KEY, HOST, cmd],
                capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
            if r.returncode == 0 or r.stdout.strip():
                return r
            last = r
        except Exception as e:
            last = e
        time.sleep(5)
    return last

# combine into one ssh: config + db counts
cmd = """cd /home/ubuntu/sba-backend && venv/bin/python - <<'EOF'
from admin.agency.sba_biztypes import get_workspace_config, list_sba_workspaces
import json
try:
    ws = list_sba_workspaces()
    print("WORKSPACES:", json.dumps(ws)[:500])
except Exception as e:
    print("WS ERR:", e)
try:
    cfg = get_workspace_config("agency")
    print("CFG:", json.dumps(cfg, default=str)[:600])
except Exception as e:
    print("CFG ERR:", e)
from admin.agency.sba_pipeline import supabase_config, load_leads
from collections import Counter
try:
    u,k = supabase_config()
    ls = load_leads(u,k)
    print("TOTAL:", len(ls))
    print("SOURCES:", dict(Counter((l.get("source") or "unknown") for l in ls)))
    print("CATS:", dict(Counter((l.get("category") or "unknown") for l in ls).most_common(8)))
except Exception as e:
    print("DB ERR:", e)
EOF"""
r = ssh(cmd)
if isinstance(r, subprocess.CompletedProcess):
    print("rc:", r.returncode)
    print(r.stdout[-2500:])
    if r.stderr.strip():
        print("STDERR:", r.stderr[-500:])
elif isinstance(r, Exception):
    print("SSH FAILED:", r)
else:
    print("NO RESULT")
