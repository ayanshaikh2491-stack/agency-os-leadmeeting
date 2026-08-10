"""Compare local vs EC2 hashes in ONE ssh call."""
import os, subprocess, sys, hashlib
sys.path.insert(0, os.getcwd())

KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

files = [
    "admin/agency/sba_autopilot.py",
    "admin/agency/sba_biztypes.py",
    "admin/tools/sba_email_client.py",
    "admin/tools/sba_meeting.py",
    "admin/workspace/agents/sba.py",
    "deploy/_backfill_websites.py",
]

# local hashes
local = {}
for f in files:
    p = os.path.join("deploy", f) if f.startswith("deploy/") else f
    if os.path.exists(p):
        local[f] = hashlib.sha256(open(p, "rb").read()).hexdigest()[:12]
    elif os.path.exists(f):
        local[f] = hashlib.sha256(open(f, "rb").read()).hexdigest()[:12]

cmd = "cd /home/ubuntu/sba-backend && " + "; ".join(f"echo {f} $(sha256sum {f} 2>/dev/null | cut -c1-12)" for f in files)
r = subprocess.run(
    ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
     "-o", "ConnectTimeout=10", "-i", KEY, HOST, cmd],
    capture_output=True, text=True, timeout=60, encoding="utf-8", errors="replace")
print("rc:", r.returncode)
for line in r.stdout.splitlines():
    parts = line.split()
    if len(parts) == 2:
        f, eh = parts
        lh = local.get(f, "NOLOCAL")
        print(f"{f}: local={lh} ec2={eh} {'SAME' if eh == lh else 'DIFF'}")
print("stderr:", r.stderr[-300:])
