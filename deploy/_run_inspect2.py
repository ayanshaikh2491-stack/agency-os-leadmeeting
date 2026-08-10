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

run(["scp", "-o", "StrictHostKeyChecking=no", "-i", KEY,
     "deploy/_ec2_inspect2.sh", HOST + ":/home/ubuntu/_ec2_inspect2.sh"], 60)
run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-i", KEY,
     HOST, "bash /home/ubuntu/_ec2_inspect2.sh"], 90)
