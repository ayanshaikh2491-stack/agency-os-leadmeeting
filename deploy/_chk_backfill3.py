"""Retry backfill state check with retries."""
import os, subprocess, sys, time, hashlib
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

lh = hashlib.sha256(open("deploy/_backfill_websites.py", "rb").read()).hexdigest()[:12]
print("local:", lh)
r = ssh("cd /home/ubuntu/sba-backend && sha256sum _backfill_websites.py | cut -c1-12")
print("ec2 hash:", r.stdout.strip() if r else "SSH_FAIL", "MATCH" if r and r.stdout.strip() == lh else "DIFF")

r = ssh("ls -la /home/ubuntu/sba-backend/_backfill.log /home/ubuntu/sba-backend/_backfill_state.json /home/ubuntu/sba-backend/.sba_backfill_state 2>&1")
print(r.stdout if r else "SSH_FAIL")

r = ssh("tail -6 /home/ubuntu/sba-backend/_backfill.log 2>/dev/null")
print("---LOG---")
print(r.stdout if r else "SSH_FAIL")
