import subprocess, os, time, datetime

os.chdir(r"C:\Users\TAUSHEF\Downloads\int")
KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

# wait until ~16:13 UTC for the next autopilot pass
target = datetime.datetime(2026, 8, 9, 16, 13, 0, tzinfo=datetime.timezone.utc)
sleep_s = (target - datetime.datetime.now(datetime.timezone.utc)).total_seconds()
if sleep_s > 0:
    print(f"sleeping {sleep_s:.0f}s until autopilot pass 16:13")
    time.sleep(min(sleep_s, 900))

def ssh(cmd, timeout=45):
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
                        "-o", "ConnectTimeout=8", "-i", KEY, HOST, cmd],
                       capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    print("rc=", r.returncode)
    print(r.stdout.strip()[:3000])
    if r.stderr.strip():
        print("ERR:", r.stderr.strip()[:400])
    return r

print("=== autopilot pass since 16:05 (full pool after fix) ===")
ssh("journalctl -u sba-autopilot.service --since '16:05' --no-pager | grep -E 'autopilot pass|lead rotation|ERROR|Traceback' | tail -8", timeout=45)
print("=== gateway errors since 16:01 ===")
ssh("journalctl -u sba-gateway.service --since '16:01' --no-pager | grep -c ' 500 ' || true", timeout=45)
