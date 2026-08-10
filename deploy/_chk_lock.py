"""Check backfill lock pidfile + chrome daemons before relaunch."""
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

r = ssh("cat /tmp/backfill_websites.pid 2>&1; echo ---; ps aux | grep -E 'backfill|sba-backfill' | grep -v grep | head -5; echo ---; systemctl is-active sba-chrome; echo ---; pgrep -af 'chrome' | grep -c chrome")
print(r.stdout if r else "SSH_FAIL")
