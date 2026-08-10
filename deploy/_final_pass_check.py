import subprocess, os, time, datetime

os.chdir(r"C:\Users\TAUSHEF\Downloads\int")
KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

target = datetime.datetime(2026, 8, 9, 15, 28, 30, tzinfo=datetime.timezone.utc)
sleep_s = (target - datetime.datetime.now(datetime.timezone.utc)).total_seconds()
if sleep_s > 0:
    print(f"sleeping {sleep_s:.0f}s")
    time.sleep(min(sleep_s, 300))

def ssh(cmd, timeout=90):
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
                        "-o", "ConnectTimeout=10", "-i", KEY, HOST, cmd],
                       capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    print("rc=", r.returncode)
    print(r.stdout.strip()[:4000])
    if r.stderr.strip():
        print("ERR:", r.stderr.strip()[:400])
    return r

print("=== autopilot pass since 15:25 (post Supabase stop) ===")
ssh("sudo journalctl -u sba-autopilot.service --since '15:25' --no-pager | grep -E 'pass|summary|emails_sent|ERROR|Traceback|CRITICAL' | tail -20")
print("=== gateway last 15 ===")
ssh("sudo journalctl -u sba-gateway.service --no-pager -n 15 | tail -15")
print("=== gateway errors ===")
ssh("sudo journalctl -u sba-gateway.service --no-pager | grep -c ' 500 ' || true")
