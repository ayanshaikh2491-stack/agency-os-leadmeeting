"""Verify autopilot recovered (no more crash-loop)."""
import os, subprocess, sys, time
sys.path.insert(0, os.getcwd())

KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=45):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
         "-o", "ConnectTimeout=10", "-i", KEY, HOST, cmd],
        capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return r

time.sleep(20)
r = ssh("systemctl show sba-autopilot -p NRestarts; systemctl is-active sba-autopilot; pgrep -af sba_autopilot | grep -v grep | head -1; echo ---; tail -3 sba_reasoning_agency.log 2>/dev/null")
print(r.stdout[-2000:])
print("rc:", r.returncode, r.stderr[-200:])
