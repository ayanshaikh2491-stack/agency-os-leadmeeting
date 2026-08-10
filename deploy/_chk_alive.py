"""Check backfill process alive + full log tail with timestamps."""
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

r = ssh("date -u +%H:%M:%S; ps -p $(cat /tmp/backfill_websites.pid 2>/dev/null) -o pid,etime,pcpu,cmd 2>/dev/null || echo PROCESS_GONE; echo ---; wc -l /tmp/backfill.log; echo ---; tail -6 /tmp/backfill.log")
print(r.stdout[-1600:])
print("rc:", r.returncode, r.stderr[-200:])
