"""Pull backfill script back from EC2 (local copy was deleted)."""
import os, subprocess, sys
sys.path.insert(0, os.getcwd())
from deploy.deploy_sba import scp

KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

r = subprocess.run(
    ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
     "-o", "ConnectTimeout=10", "-i", KEY, HOST,
     "cp /home/ubuntu/sba-backend/_backfill_websites.py /home/ubuntu/sba-backend/deploy_backfill_websites.py && wc -l /home/ubuntu/sba-backend/deploy_backfill_websites.py"],
    capture_output=True, text=True, timeout=60, encoding="utf-8", errors="replace")
print("ssh:", r.returncode, r.stdout[-300:])

r = subprocess.run(
    ["scp", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
     "-o", "ConnectTimeout=10", "-i", KEY,
     f"{HOST}:/home/ubuntu/sba-backend/deploy_backfill_websites.py",
     os.path.join(os.getcwd(), "deploy", "_backfill_websites.py")],
    capture_output=True, text=True, timeout=120, encoding="utf-8", errors="replace")
print("scp back:", r.returncode, r.stderr[-300:])
