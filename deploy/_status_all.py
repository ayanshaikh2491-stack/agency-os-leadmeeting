"""scp db counts script to EC2, then run status check."""
import subprocess, os, sys
sys.path.insert(0, os.getcwd())
KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

r = subprocess.run(
    ["scp", "-o", "StrictHostKeyChecking=no", "-i", KEY,
     "deploy/_db_counts_remote.py", HOST + ":/home/ubuntu/sba-backend/_db_counts_remote.py"],
    capture_output=True, text=True, timeout=60)
print("scp rc=", r.returncode, (r.stderr or "")[:300])
subprocess.run([sys.executable, "deploy/_chk_status_now.py"])
