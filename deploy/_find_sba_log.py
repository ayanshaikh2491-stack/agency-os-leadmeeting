"""Find sba service log location and tail it for agent errors."""
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

r = ssh("cat /etc/systemd/system/sba.service 2>/dev/null | grep -E 'ExecStart|StandardOutput|StandardError'")
print("=== sba.service ===")
print((r.stdout or ""))

r = ssh("ls -la /home/ubuntu/sba-backend/*.log 2>/dev/null; ls -la /var/log/sba* 2>/dev/null | head")
print("=== log files ===")
print((r.stdout or ""))
