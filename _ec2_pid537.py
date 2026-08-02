import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=60):
    full = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=8",
            "-i", KEY, HOST, cmd]
    r = subprocess.run(full, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return r

r = ssh("ps -p 537 -o pid,user,cmd --no-headers 2>/dev/null; echo ====; systemctl list-units --type=service --all --no-legend | grep -i 'agency\\|sba\\|backend\\|platform' ; echo ====; ls /etc/systemd/system/ | grep -i 'agency\\|sba\\|backend'")
print(r.stdout[:2500])
if r.stderr.strip():
    print("ERR:", r.stderr[-300:])
