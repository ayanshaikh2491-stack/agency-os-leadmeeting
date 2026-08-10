"""Check autopilot health: log window 400s + DB counts + enrichment state."""
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

# autopilot process + recent log lines
r = ssh("ps aux | grep [a]utopilot | grep -v grep | head -3; echo ---; ls -t /home/ubuntu/sba-backend/*.log 2>/dev/null | head -5; echo ---; tail -25 /home/ubuntu/sba-backend/autopilot.log 2>/dev/null || tail -25 /tmp/*autopilot*.log 2>/dev/null || find /home/ubuntu/sba-backend -name '*autopilot*' -newer /tmp/backfill.log 2>/dev/null | head")
print(r.stdout[-4000:])
print("rc:", r.returncode, r.stderr[-300:])
