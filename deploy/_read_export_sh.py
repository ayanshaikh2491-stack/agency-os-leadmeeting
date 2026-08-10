import subprocess, os

os.chdir(r"C:\Users\TAUSHEF\Downloads\int")
KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
                    "-o", "ConnectTimeout=10", "-i", KEY, HOST, "cat /home/ubuntu/_pb_export.sh"],
                   capture_output=True, text=True, timeout=30, encoding="utf-8", errors="replace")
print("rc=", r.returncode)
print(r.stdout)
