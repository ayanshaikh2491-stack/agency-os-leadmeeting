import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

def run(remote_cmd, timeout=90):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-i", KEY, HOST, remote_cmd],
        capture_output=True, text=True, timeout=timeout,
    )
    print(r.stdout)
    if r.stderr:
        print("STDERR:", r.stderr[:500])
    print("rc=", r.returncode)
    return r

# Full traceback around the warning at 16:16:48
run("sudo journalctl -u sba-autopilot.service --since '2026-08-09 16:15:00' --until '2026-08-09 16:18:00' --no-pager | tail -60")

# Also check if the error repeats on earlier passes
run("sudo journalctl -u sba-autopilot.service --since '2026-08-09 15:20:00' --no-pager | grep -c \"'int' object has no attribute 'strip'\"")
