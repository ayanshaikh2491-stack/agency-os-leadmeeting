"""Deploy agent_persistence.py to EC2 and run the saver test."""
import os, subprocess, sys, time
sys.path.insert(0, os.getcwd())

KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"
LOCAL = os.path.join(os.getcwd(), "admin", "agency", "agent_persistence.py")
REMOTE = "/home/ubuntu/sba-backend/admin/agency/agent_persistence.py"
TEST = os.path.join(os.getcwd(), "deploy", "_test_saver_ec2.py")
REMOTE_TEST = "/home/ubuntu/sba-backend/_test_saver_ec2.py"

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

print("== scp file ==")
r = scp(LOCAL, REMOTE)
print("scp agent_persistence:", "OK" if r and r.returncode == 0 else r)

r = scp(TEST, REMOTE_TEST)
print("scp test:", "OK" if r and r.returncode == 0 else r)

print("== py_compile on server ==")
r = ssh("cd /home/ubuntu/sba-backend && venv/bin/python -m py_compile admin/agency/agent_persistence.py && echo COMPILE_OK")
print(r.stdout if r else "NO OUTPUT", (r.stderr or "")[-400:])

print("== run saver test ==")
r = ssh("cd /home/ubuntu/sba-backend && venv/bin/python _test_saver_ec2.py")
print((r.stdout or "")[-3000:])
if r.stderr and r.stderr.strip():
    print("STDERR:", r.stderr[-1500:])
