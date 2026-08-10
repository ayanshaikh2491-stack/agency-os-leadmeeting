import subprocess, os

os.chdir(r"C:\Users\TAUSHEF\Downloads\int")
KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
                    "-o", "ConnectTimeout=10", "-i", KEY, HOST, "echo HELLO; uptime"],
                   capture_output=True, text=True, timeout=30, encoding="utf-8", errors="replace")
print("rc=", r.returncode)
print("OUT:", r.stdout.strip()[:1000])
print("ERR:", r.stderr.strip()[:500])
