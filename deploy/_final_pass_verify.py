import subprocess, os, time

os.chdir(r"C:\Users\TAUSHEF\Downloads\int")
KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

time.sleep(30)

def ssh(cmd, timeout=45):
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
                        "-o", "ConnectTimeout=8", "-i", KEY, HOST, cmd],
                       capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    print("rc=", r.returncode)
    print(r.stdout.strip()[:3000])
    if r.stderr.strip():
        print("ERR:", r.stderr.strip()[:400])
    return r

print("=== autopilot latest passes ===")
ssh("journalctl -u sba-autopilot.service --since '16:10' --no-pager | grep -E 'autopilot pass|lead rotation|ERROR|Traceback' | tail -8", timeout=45)
print("=== gateway requests since 16:10 (page loop evidence) ===")
ssh("journalctl -u sba-gateway.service --since '16:10' --no-pager | grep -E 'GET /rest/v1/leads' | head -8", timeout=45)
print("=== gateway 500 count today ===")
ssh("journalctl -u sba-gateway.service --no-pager | grep -c ' 500 ' || true", timeout=45)
