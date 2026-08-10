"""Check if autopilot is crash-looping (import error) after my deploy."""
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

# systemd restart count + recent journal
r = ssh("systemctl show sba-autopilot -p NRestarts -p ExecMainStartTimestamp -p ActiveEnterTimestamp; echo ---; journalctl -u sba-autopilot --no-pager -n 15 2>&1 | tail -15")
print(r.stdout[-3000:])
print("rc:", r.returncode, r.stderr[-200:])
