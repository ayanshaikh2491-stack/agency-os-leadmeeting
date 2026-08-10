import subprocess, os, time

os.chdir(r"C:\Users\TAUSHEF\Downloads\int")
KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

# Wait until ~15:27 so autopilot's first full pass on new env completes
now = time.time()
wait = max(0, (time.time() - now))  # placeholder
# sleep until 15:27 UTC
import datetime
target = datetime.datetime(2026, 8, 9, 15, 27, 0, tzinfo=datetime.timezone.utc)
sleep_s = (target - datetime.datetime.now(datetime.timezone.utc)).total_seconds()
if sleep_s > 0:
    print(f"sleeping {sleep_s:.0f}s until autopilot pass")
    time.sleep(min(sleep_s, 300))

cmds = [
    "echo '=== autopilot last 40 ==='; sudo journalctl -u sba-autopilot.service --since '15 minutes ago' --no-pager | tail -40",
    "echo '=== gateway journal last 25 ==='; sudo journalctl -u sba-gateway.service --no-pager -n 25 | tail -25",
    "echo '=== gateway 500 count ==='; sudo journalctl -u sba-gateway.service --no-pager | grep -c ' 500 '",
]
for cmd in cmds:
    print("=" * 30)
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
                        "-o", "ConnectTimeout=10", "-i", KEY, HOST, cmd],
                       capture_output=True, text=True, timeout=90, encoding="utf-8", errors="replace")
    print("rc=", r.returncode)
    print(r.stdout.strip()[:5000])
    if r.stderr.strip():
        print("ERR:", r.stderr.strip()[:400])
