"""Run agent chat tests on EC2 (gateway at 127.0.0.1:8095)."""
import os, subprocess, sys, time
sys.path.insert(0, os.getcwd())

KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"
LOCAL = os.path.join(os.getcwd(), "deploy", "_restart_and_test_agents.py")
REMOTE = "/home/ubuntu/sba-backend/_test_agents_live.py"

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

# run only the agent chat part on server (restart already done)
r = ssh("cd /home/ubuntu/sba-backend && venv/bin/python _test_agents_live.py 2>&1 | tail -60")
print((r.stdout or "")[-5000:])
if r.stderr and r.stderr.strip():
    print("STDERR:", r.stderr[-800:])
