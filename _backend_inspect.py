import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=60):
    full = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10",
            "-i", KEY, HOST, cmd]
    r = subprocess.run(full, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return r

r = ssh("ls -la /opt/agency-platform/backend/ 2>/dev/null | head -30; echo ====; cat /opt/agency-platform/backend/.env 2>/dev/null | grep -v 'KEY\\|SECRET\\|PASS\\|TOKEN' | head -30; echo ====ENV_FULL_LINES; wc -l /opt/agency-platform/backend/.env 2>/dev/null")
print(r.stdout[:3500])
if r.stderr.strip():
    print("ERR:", r.stderr[-400:])
