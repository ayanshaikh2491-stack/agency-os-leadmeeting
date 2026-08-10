import subprocess, os, sys

os.chdir(r"C:\Users\TAUSHEF\Downloads\int")
KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def run(args, timeout=45):
    r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    print(r.stdout)
    if r.stderr:
        print("STDERR:", r.stderr[:500])
    print("rc=", r.returncode)
    return r

run(["scp", "-o", "StrictHostKeyChecking=no", "-i", KEY,
     "deploy/_diag.sh", HOST + ":/home/ubuntu/_diag.sh"], 45)
run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-i", KEY,
     HOST, "bash /home/ubuntu/_diag.sh"], 45)
