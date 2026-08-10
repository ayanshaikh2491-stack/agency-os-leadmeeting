"""Deploy sba_reason.py + restart autopilot service, verify recovery."""
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

# 1. syntax + deploy
r = ssh("cd /home/ubuntu/sba-backend && venv/bin/python -m py_compile admin/agency/sba_reason.py && echo SYNTAX_OK")
print("syntax:", r.returncode, r.stdout.strip()[-40:])
r = scp("admin/agency/sba_reason.py", "/home/ubuntu/sba-backend/admin/agency/sba_reason.py", timeout=120)
print("scp rc:", r.returncode)

# 2. restart autopilot (systemd service)
r = ssh("systemctl is-active sba-autopilot 2>/dev/null || echo NOT_A_SERVICE; systemctl list-units --type=service 2>/dev/null | grep -i sba | head")
print("service check:", r.stdout.strip()[-300:])

r = ssh("systemctl restart sba-autopilot 2>&1; echo RC=$?; sleep 5; systemctl is-active sba-autopilot; pgrep -af sba_autopilot | grep -v grep | head -2")
print("restart:", r.stdout.strip()[-400:])
