"""Check backfill state on EC2: file present? hash same? state file? any running?"""
import os, subprocess, sys, hashlib
sys.path.insert(0, os.getcwd())

KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=45):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
         "-o", "ConnectTimeout=10", "-i", KEY, HOST, cmd],
        capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return r

# local hash
p = "deploy/_backfill_websites.py"
lh = hashlib.sha256(open(p, "rb").read()).hexdigest()[:12] if os.path.exists(p) else "NOLOCAL"
print("local hash:", lh)

r = ssh("cd /home/ubuntu/sba-backend && ls -la deploy/_backfill_websites.py 2>&1; echo ---; sha256sum deploy/_backfill_websites.py 2>/dev/null | cut -c1-12; echo ---; ls -la deploy/_backfill.log 2>&1; echo ---; pgrep -af backfill | grep -v grep | head -3; echo ---; ls -la deploy/_backfill_state.json 2>&1; cat deploy/_backfill_state.json 2>/dev/null | head -5")
print(r.stdout[-2500:])
print("rc:", r.returncode, r.stderr[-200:])
