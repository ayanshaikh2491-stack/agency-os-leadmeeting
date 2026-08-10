"""STOP backfill immediately (junk emails patching), then list recent patches."""
import os, subprocess, sys
sys.path.insert(0, os.getcwd())

KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=45):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
         "-o", "ConnectTimeout=10", "-i", KEY, HOST, cmd],
        capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return r

# kill by pidfile (safe, won't match this ssh)
r = ssh("kill $(cat /tmp/backfill_websites.pid 2>/dev/null) 2>/dev/null; sleep 2; kill -9 $(cat /tmp/backfill_websites.pid 2>/dev/null) 2>/dev/null; ps -p $(cat /tmp/backfill_websites.pid 2>/dev/null) >/dev/null 2>&1 && echo STILL_ALIVE || echo STOPPED")
print("stop:", r.stdout.strip()[-80:])

# list all EMAIL lines from the log to audit junk
r = ssh("grep -E 'EMAIL|no email' /tmp/backfill.log | tail -40")
print(r.stdout[-4000:])
