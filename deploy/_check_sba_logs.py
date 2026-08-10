"""Check sba service logs for agent chat failures."""
import os, subprocess, sys
sys.path.insert(0, os.getcwd())

KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=60):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
         "-o", "ConnectTimeout=15", "-i", KEY, HOST, cmd],
        capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return r

# journalctl for sba service - look for agent errors
r = ssh("journalctl -u sba.service --since '10 min ago' --no-pager 2>/dev/null | grep -iE 'agent|error|exception|traceback' | tail -40")
print("=== sba journal (agent/error lines) ===")
print((r.stdout or "")[-4000:])
print("STDERR:", (r.stderr or "")[-300:])
