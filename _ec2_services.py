import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=60):
    full = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=8",
            "-i", KEY, HOST, cmd]
    r = subprocess.run(full, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return r

r = ssh("echo '=== agency-scheduler ==='; cat /etc/systemd/system/agency-scheduler.service 2>/dev/null | grep -E 'WorkingDir|EnvironmentFile|ExecStart'; echo '=== sba-agent ==='; cat /etc/systemd/system/sba-agent.service 2>/dev/null | grep -E 'WorkingDir|EnvironmentFile|ExecStart'; echo '=== sba.service ==='; cat /etc/systemd/system/sba.service 2>/dev/null | grep -E 'WorkingDir|EnvironmentFile|ExecStart'; echo '=== home agency-platform ==='; ls -la /home/ubuntu/agency-platform 2>&1 | head -5")
print(r.stdout[:3000])
if r.stderr.strip():
    print("ERR:", r.stderr[-300:])
