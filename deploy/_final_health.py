"""Final health sweep: services, autopilot, backend health."""
import os, subprocess, sys, time
sys.path.insert(0, os.getcwd())

KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def run(args, timeout=90, tries=3):
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

print("== services ==")
r = ssh("systemctl is-active sba.service sba-gateway.service sba-autopilot.service sba-chrome.service pocketbase.service")
print((r.stdout or "").strip())

print("== /api/health ==")
r = ssh("curl -s -m 10 http://127.0.0.1:8000/api/health | head -c 300")
print((r.stdout or "").strip()[:300])

print("== autopilot recent pass ==")
r = ssh("cd /home/ubuntu/sba-backend && ls -t state/autopilot*.json 2>/dev/null | head -1 && cat $(ls -t state/autopilot*.json 2>/dev/null | head -1) 2>/dev/null | head -c 400")
print((r.stdout or "").strip()[:400])

print("== sba.log last 5 lines ==")
r = ssh("sudo tail -5 /var/log/sba.log 2>/dev/null")
print((r.stdout or "").strip()[:600])
