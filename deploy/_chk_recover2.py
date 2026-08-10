"""Deep check: pid alive? last crashes? fresh log lines?"""
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

time.sleep(30)
r = ssh("cd /home/ubuntu/sba-backend && ps -p 2338087 -o pid,etime,cmd --no-headers; echo ---ALIVE---; systemctl is-active sba-autopilot; systemctl show sba-autopilot -p NRestarts; echo ---JOURNAL---; journalctl -u sba-autopilot --no-pager -n 8 2>&1 | tail -8; echo ---LOG---; tail -3 sba_reasoning_agency.log")
print(r.stdout[-3000:])
print("rc:", r.returncode, r.stderr[-200:])
