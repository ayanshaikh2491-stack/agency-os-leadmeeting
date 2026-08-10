"""scp + run deep crawl diagnosis on EC2."""
import subprocess, sys, os
sys.path.insert(0, os.getcwd())
KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=180):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
         "-o", "ConnectTimeout=15", "-i", KEY, HOST, cmd],
        capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return r

r = subprocess.run(
    ["scp", "-o", "StrictHostKeyChecking=no", "-i", KEY,
     "deploy/_diag_crawl.py", HOST + ":/home/ubuntu/sba-backend/_diag_crawl.py"],
    capture_output=True, text=True, timeout=60)
print("scp rc=", r.returncode, (r.stderr or "")[:200])
r = ssh("cd /home/ubuntu/sba-backend && python3 _diag_crawl.py", timeout=180)
print(r.stdout)
if r.stderr.strip():
    print("STDERR:", r.stderr[:800])
