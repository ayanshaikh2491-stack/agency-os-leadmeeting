import subprocess, sys

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=40):
    full = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=15",
            "-i", KEY, HOST, cmd]
    r = subprocess.run(full, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return r

r = ssh("echo CONNECTED; hostname; uptime; free -m; df -h /; cat /etc/os-release | head -2")
print("EXIT:", r.returncode)
print(r.stdout)
if r.stderr.strip():
    print("STDERR:", r.stderr[-1500:])
