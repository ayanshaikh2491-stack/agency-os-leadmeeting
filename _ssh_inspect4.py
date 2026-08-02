import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=25):
    full = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=12",
            "-i", KEY, HOST, cmd]
    r = subprocess.run(full, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return r

cmds = [
    ("opt backend dir", "ls -la /opt/agency-platform/backend 2>&1 | head -30; echo ---; ls -la /opt/agency-platform/backend/.env 2>&1"),
    ("service agency-backend", "cat /etc/systemd/system/agency-backend.service 2>&1"),
    ("service sba-agent", "cat /etc/systemd/system/sba-agent.service 2>&1"),
    ("service scheduler", "cat /etc/systemd/system/agency-scheduler.service 2>&1"),
    ("opt docker-compose", "ls /opt/agency-platform 2>&1; echo ---; ls /opt 2>&1"),
]
for name, cmd in cmds:
    print(f"===== {name} =====")
    r = ssh(cmd, timeout=28)
    print(r.stdout[:3000])
    if r.stderr.strip():
        print("STDERR:", r.stderr[-600:])
    print()
