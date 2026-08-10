import sys, os, subprocess
sys.path.insert(0, os.getcwd())
from deploy.deploy_sba import scp

KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

r = scp("deploy/_chk_statefile.py", "/home/ubuntu/sba-backend/_chk_statefile.py", timeout=120)
print("scp rc:", r.returncode)
r2 = subprocess.run(
    ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
     "-o", "ConnectTimeout=10", "-i", KEY, HOST,
     "cd /home/ubuntu/sba-backend && timeout 30 venv/bin/python _chk_statefile.py 2>&1; echo RC=$?"],
    capture_output=True, text=True, timeout=90, encoding="utf-8", errors="replace")
print(r2.stdout[-2000:])
print(r2.stderr[-300:])
