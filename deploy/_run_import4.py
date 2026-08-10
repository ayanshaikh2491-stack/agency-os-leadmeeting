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

# launch idempotent import (now with page fix, dedup works across pages)
run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
     "-i", KEY, HOST, "nohup bash /tmp/_remote_import2.sh > /tmp/pb_import_run3.log 2>&1 & echo STARTED"])
