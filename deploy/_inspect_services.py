"""Inspect sba.service + sba-gateway.service config, ports, gateway proxy."""
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

def show(title, cmd, n=4000):
    print(f"\n===== {title} =====")
    r = ssh(cmd)
    if isinstance(r, subprocess.CompletedProcess):
        print((r.stdout or "").strip()[:n] or "(no output) rc=%s" % r.returncode)
        if r.stderr and r.stderr.strip():
            print("STDERR:", r.stderr.strip()[:600])
    else:
        print("SSH FAILED:", r)

show("sba.service unit", "systemctl cat sba.service 2>&1 | head -40")
show("sba-gateway.service unit", "systemctl cat sba-gateway.service 2>&1 | head -40")
show("listening ports", "sudo ss -tlnp 2>/dev/null | grep -E ':8000|:8090|:8095|:8050' || netstat -tlnp 2>/dev/null | grep -E ':8000|:8090|:8095|:8050'")
show("sba.service recent logs", "sudo journalctl -u sba.service -n 25 --no-pager 2>&1 | tail -25")
show("sba-gateway recent logs", "sudo journalctl -u sba-gateway.service -n 15 --no-pager 2>&1 | tail -15")
