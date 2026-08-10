import subprocess, os, sys

os.chdir(r"C:\Users\TAUSHEF\Downloads\int")
KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def run(args, timeout=120):
    r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    print(r.stdout)
    if r.stderr:
        print("STDERR:", r.stderr[:800])
    print("rc=", r.returncode)
    return r

# 1. upload patched gateway + importer
run(["scp", "-o", "StrictHostKeyChecking=no", "-i", KEY,
     "deploy/pb_gateway.py", HOST + ":/home/ubuntu/sba-backend/pb_gateway.py"], 60)
run(["scp", "-o", "StrictHostKeyChecking=no", "-i", KEY,
     "deploy/_pb_import.py", HOST + ":/home/ubuntu/sba-backend/_pb_import.py"], 60)
# 2. restart gateway
run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-i", KEY,
     HOST, "bash /home/ubuntu/_gw_launch2.sh"], 60)
