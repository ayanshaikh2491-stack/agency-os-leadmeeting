"""Deploy persistence fix, create missing PB collections, restart service, verify."""
import os, subprocess, sys, time
sys.path.insert(0, os.getcwd())

KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"
LOCAL = os.path.join(os.getcwd(), "admin", "agency", "agent_persistence.py")
REMOTE = "/home/ubuntu/sba-backend/admin/agency/agent_persistence.py"
TEST = os.path.join(os.getcwd(), "deploy", "_test_saver_ec2.py")
REMOTE_TEST = "/home/ubuntu/sba-backend/_test_saver_ec2.py"
CREATE_COLS = os.path.join(os.getcwd(), "deploy", "_pb_create_missing_agent_cols.py")
REMOTE_CREATE = "/home/ubuntu/sba-backend/_pb_create_missing_agent_cols.py"

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

print("== scp ==")
for src, dst in [(LOCAL, REMOTE), (TEST, REMOTE_TEST), (CREATE_COLS, REMOTE_CREATE)]:
    r = scp(src, dst)
    print("scp", os.path.basename(src), ":", "OK" if r and r.returncode == 0 else r)

print("== py_compile ==")
r = ssh("cd /home/ubuntu/sba-backend && venv/bin/python -m py_compile admin/agency/agent_persistence.py && echo COMPILE_OK")
print(r.stdout if r else "NO OUTPUT", (r.stderr or "")[-300:])

print("== create missing PB collections ==")
r = ssh("cd /home/ubuntu/sba-backend && python3 _pb_create_missing_agent_cols.py")
print((r.stdout or "")[-2500:])
if r.stderr and r.stderr.strip():
    print("STDERR:", r.stderr[-600:])

print("== run saver test (writes should persist now) ==")
r = ssh("cd /home/ubuntu/sba-backend && venv/bin/python _test_saver_ec2.py")
print((r.stdout or "")[-2500:])
if r.stderr and r.stderr.strip():
    print("STDERR:", r.stderr[-1200:])
