"""If pidfile stale, relaunch backfill with nohup logging to _backfill.log."""
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

# is old pid alive?
r = ssh("kill -0 2246371 2>&1 && echo ALIVE || echo DEAD")
print("old pid:", r.stdout.strip() if r else "SSH_FAIL")

if r and "ALIVE" in r.stdout:
    print("backfill already running; no relaunch")
    sys.exit(0)

# stale -> clear pidfile and launch
r = ssh("rm -f /tmp/backfill_websites.pid && cd /home/ubuntu/sba-backend && nohup venv/bin/python _backfill_websites.py > _backfill.log 2>&1 & echo LAUNCHED pid $!")
print(r.stdout if r else "SSH_FAIL")
time.sleep(15)
r = ssh("cat /tmp/backfill_websites.pid; echo ---; head -15 /home/ubuntu/sba-backend/_backfill.log")
print(r.stdout if r else "SSH_FAIL")
