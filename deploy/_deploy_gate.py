"""Deploy gate fix: junk lists (autopilot) + backfill gate. Then cleanup junk rows."""
import os, subprocess, sys, time
sys.path.insert(0, os.getcwd())
from deploy.deploy_sba import scp

KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=45):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
         "-o", "ConnectTimeout=10", "-i", KEY, HOST, cmd],
        capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return r

# 1. syntax + deploy both files
r = ssh("cd /home/ubuntu/sba-backend && venv/bin/python -m py_compile admin/agency/sba_autopilot.py && echo OK1")
print("autopilot syntax:", r.returncode, r.stdout.strip()[-40:])
for f, dest in [("admin/agency/sba_autopilot.py", "admin/agency/sba_autopilot.py"),
                ("deploy/_backfill_websites.py", "_backfill_websites.py")]:
    r = scp(f, f"/home/ubuntu/sba-backend/{dest}", timeout=120)
    print("scp", f, "->", dest, "rc:", r.returncode)

# 2. restart autopilot with new junk lists
r = ssh("sudo -n systemctl restart sba-autopilot 2>&1; echo RC=$?")
print("restart:", r.stdout.strip()[-100:])
time.sleep(6)
r = ssh("systemctl is-active sba-autopilot; pgrep -af sba_autopilot | grep -v grep | head -1")
print("after:", r.stdout.strip()[-150:])
