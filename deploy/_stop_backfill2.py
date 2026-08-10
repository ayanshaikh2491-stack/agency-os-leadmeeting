"""Stop second backfill instance via pidfile + explicit pid. Never pkill."""
import os, subprocess, sys, time
sys.path.insert(0, os.getcwd())

KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=60, tries=4):
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
        time.sleep(4)
    return last

# read pidfile
r = ssh("cat /tmp/backfill_websites.pid 2>&1; echo; pgrep -f _backfill_websites")
print("PIDFILE + PROCS:")
print(r.stdout if r and r.stdout.strip() else "SSH_FAIL")

# kill pidfile pid + any leftover explicit pids (except this ssh's grep)
if isinstance(r, subprocess.CompletedProcess):
    lines = r.stdout.strip().splitlines()
    pids = set()
    if lines and lines[0].strip().isdigit():
        pids.add(lines[0].strip())
    for ln in lines[1:]:
        for tok in ln.split():
            if tok.isdigit():
                pids.add(tok)
    if pids:
        killcmd = " && ".join(f"kill -9 {p} 2>/dev/null; echo killed {p}" for p in sorted(pids))
        r2 = ssh(f"cd /home/ubuntu/sba-backend && {killcmd}; sleep 2; rm -f /tmp/backfill_websites.pid; pgrep -f _backfill_websites || echo NONE_RUNNING")
        print("KILL RESULT:")
        print(r2.stdout if r2 and r2.stdout.strip() else "SSH_FAIL2")
