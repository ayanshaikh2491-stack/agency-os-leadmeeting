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

# First check venv has fastapi+uvicorn, then deploy
run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-i", KEY,
     HOST, "/home/ubuntu/sba-backend/venv/bin/python -c 'import fastapi, uvicorn; print(\"fastapi\", fastapi.__version__, \"uvicorn OK\")'"], 60)
run(["scp", "-o", "StrictHostKeyChecking=no", "-i", KEY,
     "deploy/pb_gateway.py", HOST + ":/home/ubuntu/sba-backend/pb_gateway.py"], 60)
run(["scp", "-o", "StrictHostKeyChecking=no", "-i", KEY,
     "deploy/_pb_gw_deploy.sh", HOST + ":/home/ubuntu/_pb_gw_deploy.sh"], 60)
run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-i", KEY,
     HOST, "bash /home/ubuntu/_pb_gw_deploy.sh"], 90)
