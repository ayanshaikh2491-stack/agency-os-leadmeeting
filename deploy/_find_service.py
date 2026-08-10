"""Restart sba service and test all 7 live agents."""
import os, subprocess, sys, time
sys.path.insert(0, os.getcwd())

KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

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

# 1. find service
print("== find service ==")
r = ssh("systemctl list-units --type=service --all | grep -iE 'sba|pb|pocket|agency' | head -20")
print((r.stdout or "").strip() or "(none)")
r = ssh("systemctl list-unit-files | grep -iE 'sba|pb|pocket|agency' | head -20")
print((r.stdout or "").strip() or "(none)")
