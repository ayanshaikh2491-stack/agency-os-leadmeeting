"""Check autopilot health after my deploy + EC2 sba_email_client diff."""
import os, subprocess, sys
sys.path.insert(0, os.getcwd())

KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=45):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
         "-o", "ConnectTimeout=10", "-i", KEY, HOST, cmd],
        capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return r

r = ssh("systemctl is-active sba-autopilot; pgrep -af sba_autopilot | grep -v grep | head -1; echo ---; grep -c build_workspace_email_client admin/tools/sba_email_client.py; echo ---; tail -5 sba_reasoning_agency.log")
print(r.stdout[-2500:])
print("rc:", r.returncode, r.stderr[-200:])
