"""Compare local vs EC2 backfill hash + find state/log."""
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

lh = hashlib.sha256(open("deploy/_backfill_websites.py", "rb").read()).hexdigest()[:12]
print("local:", lh)
r = ssh("cd /home/ubuntu/sba-backend && sha256sum _backfill_websites.py | cut -c1-12; echo ---; ls -la .sba_backfill_state* _backfill.log _backfill_state.json 2>&1; echo ---; cat _backfill_state.json 2>/dev/null | head -c 600; echo; echo ---LOG---; tail -8 _backfill.log 2>/dev/null")
print(r.stdout[-2500:])
print("rc:", r.returncode, r.stderr[-200:])
