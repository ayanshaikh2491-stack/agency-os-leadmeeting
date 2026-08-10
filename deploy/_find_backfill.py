"""Find backfill script + logs on EC2."""
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

r = ssh("find /home/ubuntu -maxdepth 4 -name '*backfill*' 2>/dev/null; echo ---; ls /home/ubuntu/sba-backend/deploy/ 2>&1; echo ---; pgrep -af '_backfill_websites' | grep -v grep; echo ---; ls -la /home/ubuntu/*.log 2>/dev/null | tail -5")
print(r.stdout[-3000:])
print("rc:", r.returncode, r.stderr[-200:])
