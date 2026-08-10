import subprocess, os

os.chdir(r"C:\Users\TAUSHEF\Downloads\int")
KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

# run idempotent import in background on remote
r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
                    "-i", KEY, HOST,
                    "nohup bash /tmp/_remote_import2.sh > /tmp/pb_import_run2.log 2>&1 & echo STARTED"],
                   capture_output=True, text=True, timeout=60, encoding="utf-8", errors="replace")
print("launch rc=", r.returncode, r.stdout.strip()[:500])
