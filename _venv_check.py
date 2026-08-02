import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=45):
    full = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10",
            "-i", KEY, HOST, cmd]
    r = subprocess.run(full, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return r

r = ssh("ls -la /home/ubuntu/agency-platform 2>&1 | head -10; echo ====; ls /home/ubuntu/agency-platform/backend 2>&1 | head -10; echo ====VENV; ls /home/ubuntu/agency-platform/backend/venv/bin/python* 2>&1 | head; ls /opt/agency-platform/backend/venv/bin/python* 2>&1 | head; echo ====WHICH_PY; which python3; python3 --version 2>&1")
print(r.stdout[:2500])
if r.stderr.strip():
    print("ERR:", r.stderr[-300:])
