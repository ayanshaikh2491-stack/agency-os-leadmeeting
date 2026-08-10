import subprocess, os

os.chdir(r"C:\Users\TAUSHEF\Downloads\int")
KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def run(args, timeout=240):
    r = subprocess.run(args, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    print("rc=", r.returncode)
    print(r.stdout.strip()[:4000])
    if r.stderr.strip():
        print("ERR:", r.stderr.strip()[:600])
    return r

# 1. fresh export from Supabase docker
run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
     "-i", KEY, HOST, "bash /home/ubuntu/_pb_export.sh"], 300)

# 2. upload idempotent import script
run(["scp", "-o", "StrictHostKeyChecking=no", "-i", KEY,
     "deploy/_pb_import.py", HOST + ":/home/ubuntu/sba-backend/_pb_import.py"], 60)
