import subprocess, os, sys

os.chdir(r"C:\Users\TAUSHEF\Downloads\int")
KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def run(args, timeout=60):
    r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    print(r.stdout)
    if r.stderr:
        print("STDERR:", r.stderr[:800])
    print("rc=", r.returncode)
    return r

run(["scp", "-o", "StrictHostKeyChecking=no", "-i", KEY,
     "deploy/_gw_env.sh", HOST + ":/home/ubuntu/_gw_env.sh"], 60)
run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-i", KEY,
     HOST, "bash /home/ubuntu/_gw_env.sh"], 60)
run(["scp", "-o", "StrictHostKeyChecking=no", "-i", KEY,
     "deploy/_gw_launch.sh", HOST + ":/home/ubuntu/_gw_launch.sh"], 60)
run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-i", KEY,
     HOST, "bash /home/ubuntu/_gw_launch.sh"], 60)
import time; time.sleep(4)
run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-i", KEY,
     HOST, "curl -sf http://127.0.0.1:8095/api/health || echo NOT_UP; echo; tail -8 /home/ubuntu/sba-backend/pb_gw.log"], 60)
