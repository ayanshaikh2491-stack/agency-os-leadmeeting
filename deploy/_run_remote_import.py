import subprocess, os, sys

os.chdir(r"C:\Users\TAUSHEF\Downloads\int")
KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

# upload import script
r = subprocess.run(["scp", "-o", "StrictHostKeyChecking=no", "-i", KEY,
                    "deploy/_remote_import.sh", HOST + ":/tmp/_remote_import.sh"],
                   capture_output=True, text=True, timeout=60, encoding="utf-8", errors="replace")
print("scp rc=", r.returncode)

# run import in background on remote, log to file
r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
                    "-i", KEY, HOST,
                    "nohup bash /tmp/_remote_import.sh > /tmp/pb_import_run.log 2>&1 & echo STARTED"],
                   capture_output=True, text=True, timeout=60, encoding="utf-8", errors="replace")
print("launch rc=", r.returncode, r.stdout.strip()[:500])
