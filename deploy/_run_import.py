import subprocess, os, sys

os.chdir(r"C:\Users\TAUSHEF\Downloads\int")
KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def run(args, timeout=600):
    r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    print(r.stdout)
    if r.stderr:
        print("STDERR:", r.stderr[:1000])
    print("rc=", r.returncode)
    return r

run(["scp", "-o", "StrictHostKeyChecking=no", "-i", KEY,
     "deploy/_pb_import_run.sh", HOST + ":/home/ubuntu/_pb_import_run.sh"], 60)
run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-i", KEY,
     HOST, "bash /home/ubuntu/_pb_import_run.sh"], 600)
