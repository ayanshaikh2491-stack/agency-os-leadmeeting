"""Poll backfill progress again (longer window)."""
import os, subprocess, sys, time
sys.path.insert(0, os.getcwd())

KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=60, tries=3):
    for i in range(tries):
        try:
            r = subprocess.run(
                ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
                 "-o", "ConnectTimeout=10", "-i", KEY, HOST, cmd],
                capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
            if r.returncode == 0 or r.stdout.strip():
                return r
        except Exception:
            pass
        time.sleep(3)
    return None

time.sleep(300)
r = ssh("cd /home/ubuntu/sba-backend && ps -p 2367341 -o pid,etime --no-headers 2>&1; echo ---; grep -E 'target |EMAIL|FINAL|DONE' _backfill.log | tail -12")
print(r.stdout if r else "SSH_FAIL")
