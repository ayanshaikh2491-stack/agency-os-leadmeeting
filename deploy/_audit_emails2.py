"""Audit all EMAIL lines in backfill log + check if second instance running."""
import os, subprocess, sys, time
sys.path.insert(0, os.getcwd())

KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=90, tries=4):
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

# all EMAIL lines + second instance check
cmd = ("cd /home/ubuntu/sba-backend && echo ===PID===; cat /tmp/backfill_websites.pid; "
       "echo; echo ===PS===; ps -p 2624133 -o pid,etime,cmd --no-headers 2>&1; "
       "echo ===HEAD===; head -6 _backfill.log; "
       "echo ===EMAILS===; grep -a 'EMAIL ' _backfill.log")
r = ssh(cmd)
if isinstance(r, subprocess.CompletedProcess):
    print(r.stdout[-4000:])
else:
    print("SSH FAILED:", r)
