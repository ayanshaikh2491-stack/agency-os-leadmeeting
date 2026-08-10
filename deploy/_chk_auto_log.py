"""Check autopilot log for fresh pass lines (post-restart)."""
import os, subprocess, sys, time
sys.path.insert(0, os.getcwd())

KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=60, tries=3):
    for i in range(tries):
        try:
            r = subprocess.run(
                ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
                 "-o", "ConnectTimeout=10", "-i", KEY, HOST, cmd],
                capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
            if r.returncode == 0 or r.stdout.strip():
                return r
        except Exception:
            pass
        time.sleep(3)
    return None

r = ssh("systemctl is-active sba-autopilot; systemctl show sba-autopilot -p NRestarts; echo ---; cd /home/ubuntu/sba-backend && tail -4 sba_reasoning_agency.log | python3 -c 'import sys,json; [print(json.loads(l).get(\"event\"), json.loads(l).get(\"ts\",\"\")[:19]) for l in sys.stdin if l.strip()]' 2>/dev/null || tail -4 sba_reasoning_agency.log")
print(r.stdout if r else "SSH_FAIL")
