import subprocess, os, time

os.chdir(r"C:\Users\TAUSHEF\Downloads\int")
KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

time.sleep(120)

def ssh(cmd, timeout=40):
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
                        "-o", "ConnectTimeout=8", "-i", KEY, HOST, cmd],
                       capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    print("rc=", r.returncode)
    print(r.stdout.strip()[:3000])
    if r.stderr.strip():
        print("ERR:", r.stderr.strip()[:400])
    return r

print("=== autopilot pass summary (16:11+) ===")
ssh("journalctl -u sba-autopilot.service --since '16:11' --no-pager | grep -E 'autopilot pass|ERROR|Traceback' | tail -6", timeout=40)
print("=== gateway 500s since 16:01 ===")
ssh("journalctl -u sba-gateway.service --since '16:01' --no-pager | grep -c ' 500 ' || true", timeout=40)
