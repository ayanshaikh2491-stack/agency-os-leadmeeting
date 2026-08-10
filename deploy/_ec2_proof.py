import subprocess, os

os.chdir(r"C:\Users\TAUSHEF\Downloads\int")
KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

cmd = "hostname; echo '---'; uname -a | head -1; echo '--- RAM ---'; free -h; echo '--- DISK ---'; df -h /"
r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
                    "-o", "ConnectTimeout=10", "-i", KEY, HOST, cmd],
                   capture_output=True, text=True, timeout=60, encoding="utf-8", errors="replace")
print("rc=", r.returncode)
print(r.stdout.strip()[:2500])
if r.stderr.strip():
    print("ERR:", r.stderr.strip()[:400])
