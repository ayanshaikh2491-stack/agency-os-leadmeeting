"""Run agent tests on EC2 against backend port 8000."""
import os, subprocess, sys, time
sys.path.insert(0, os.getcwd())

KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"
LOCAL = os.path.join(os.getcwd(), "deploy", "_test_agents_8000.py")
REMOTE = "/home/ubuntu/sba-backend/_test_agents_8000.py"

def run(args, timeout=120, tries=3):
    last = None
    for i in range(tries):
        try:
            r = subprocess.run(args, capture_output=True, text=True, timeout=timeout,
                               encoding="utf-8", errors="replace")
            if r.returncode == 0 or r.stdout.strip():
                return r
            last = r
        except Exception as e:
            last = e
        time.sleep(3)
    return last

ssh = lambda cmd: run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
                       "-o", "ConnectTimeout=20", "-i", KEY, HOST, cmd])
scp = lambda src, dst: run(["scp", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
                            "-i", KEY, src, f"{HOST}:{dst}"])

r = scp(LOCAL, REMOTE)
print("scp:", "OK" if r and r.returncode == 0 else r)

r = ssh("cd /home/ubuntu/sba-backend && venv/bin/python _test_agents_8000.py 2>&1 | tail -60")
print((r.stdout or "")[-6000:])
if r.stderr and r.stderr.strip():
    print("STDERR:", r.stderr[-1000:])
