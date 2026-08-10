"""URGENT: deploy local sba_email_client.py to fix autopilot crash-loop."""
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

# deploy local sba_email_client.py (has build_workspace_email_client)
r = ssh("cd /home/ubuntu/sba-backend && venv/bin/python -m py_compile admin/tools/sba_email_client.py 2>&1 && echo SYNTAX_OK", timeout=60)
print("EC2 local syntax:", r.returncode, r.stdout.strip()[-60:], r.stderr[-200:])

r = scp("admin/tools/sba_email_client.py", "/home/ubuntu/sba-backend/admin/tools/sba_email_client.py", timeout=120)
print("scp email_client rc:", r.returncode)

# verify import works
r = ssh("cd /home/ubuntu/sba-backend && venv/bin/python -c \"import admin.tools.sba_email_client; print('IMPORT_OK')\"", timeout=60)
print("import:", r.stdout.strip()[-60:], r.returncode, r.stderr[-300:])
