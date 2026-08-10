import subprocess, os

os.chdir(r"C:\Users\TAUSHEF\Downloads\int")
KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def run(args, timeout=60):
    r = subprocess.run(args, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    print("rc=", r.returncode)
    print(r.stdout.strip()[:1500])
    if r.stderr.strip():
        print("ERR:", r.stderr.strip()[:500])
    return r

# 1. upload idempotent import script + launcher
run(["scp", "-o", "StrictHostKeyChecking=no", "-i", KEY,
     "deploy/_pb_import.py", HOST + ":/home/ubuntu/sba-backend/_pb_import.py"])
run(["scp", "-o", "StrictHostKeyChecking=no", "-i", KEY,
     "deploy/_remote_import2.sh", HOST + ":/tmp/_remote_import2.sh"])

# 2. launch in background
run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
     "-i", KEY, HOST, "nohup bash /tmp/_remote_import2.sh > /tmp/pb_import_run2.log 2>&1 & echo STARTED"])
