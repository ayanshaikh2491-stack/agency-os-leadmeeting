import subprocess, os, time

os.chdir(r"C:\Users\TAUSHEF\Downloads\int")
KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

# Wait ~3 min for autopilot to do a scrape pass, then check gateway logs + autopilot
time.sleep(180)

cmds = [
    "echo '=== gateway journal (last 30) ==='; sudo journalctl -u sba-gateway.service --no-pager -n 30 | tail -30",
    "echo '=== gateway 500 count since start ==='; sudo journalctl -u sba-gateway.service --no-pager | grep -c ' 500 '",
    "echo '=== autopilot recent ==='; sudo journalctl -u sba-autopilot.service --since '4 minutes ago' --no-pager | tail -25",
]
for cmd in cmds:
    print("=" * 30)
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
                        "-o", "ConnectTimeout=10", "-i", KEY, HOST, cmd],
                       capture_output=True, text=True, timeout=90, encoding="utf-8", errors="replace")
    print("rc=", r.returncode)
    print(r.stdout.strip()[:4000])
    if r.stderr.strip():
        print("ERR:", r.stderr.strip()[:400])
