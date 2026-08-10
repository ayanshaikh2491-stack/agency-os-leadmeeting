"""scp probe_ws + run on EC2."""
import os, subprocess, sys, time
sys.path.insert(0, os.getcwd())

KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def scp(src, dst, tries=3):
    for i in range(tries):
        try:
            r = subprocess.run(
                ["scp", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
                 "-o", "ConnectTimeout=15", "-i", KEY, src, f"{HOST}:{dst}"],
                capture_output=True, text=True, timeout=90, encoding="utf-8", errors="replace")
            if r.returncode == 0:
                return r
        except Exception:
            pass
        time.sleep(4)
    return None

def ssh(cmd, timeout=120, tries=4):
    last = None
    for i in range(tries):
        try:
            r = subprocess.run(
                ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
                 "-o", "ConnectTimeout=15", "-i", KEY, HOST, cmd],
                capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
            if r.returncode == 0 or r.stdout.strip():
                return r
            last = r
        except Exception as e:
            last = e
        time.sleep(5)
    return last

r = scp("deploy/_probe_ws.py", "/home/ubuntu/sba-backend/_probe_ws.py")
print("scp:", r.returncode if r else "FAIL")
r2 = ssh("cd /home/ubuntu/sba-backend && venv/bin/python _probe_ws.py 2>&1")
if isinstance(r2, subprocess.CompletedProcess):
    print(r2.stdout[-3000:])
    if r2.stderr.strip():
        print("STDERR:", r2.stderr[-400:])
else:
    print("SSH FAILED:", r2)
