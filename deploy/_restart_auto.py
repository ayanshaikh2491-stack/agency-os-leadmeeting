"""Restart autopilot: try sudo, fallback to kill (systemd Restart=always)."""
import os, subprocess, sys, time
sys.path.insert(0, os.getcwd())

KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=45):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
         "-o", "ConnectTimeout=10", "-i", KEY, HOST, cmd],
        capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return r

# try sudo -n (passwordless)
r = ssh("sudo -n systemctl restart sba-autopilot 2>&1; echo RC=$?")
print("sudo:", r.stdout.strip()[-200:])

if "RC=0" in r.stdout:
    time.sleep(8)
    r2 = ssh("systemctl is-active sba-autopilot; pgrep -af sba_autopilot | grep -v grep | head -2")
    print("after sudo restart:", r2.stdout.strip()[-300:])
else:
    # fallback: kill pid -> systemd restarts with new code
    r2 = ssh("pkill -f 'admin.agency.sba_autopilot' 2>&1; echo KILLED; sleep 12; systemctl is-active sba-autopilot; pgrep -af sba_autopilot | grep -v grep | head -2")
    print("kill-fallback:", r2.stdout.strip()[-300:])
