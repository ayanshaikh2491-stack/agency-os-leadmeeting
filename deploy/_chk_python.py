"""Check which python the autopilot service uses + test import there."""
import subprocess, sys, os, time
sys.path.insert(0, os.getcwd())
KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=60, tries=3):
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
        time.sleep(3)
    return last

def show(title, cmd):
    print(f"\n=== {title} ===")
    r = ssh(cmd)
    if isinstance(r, subprocess.CompletedProcess):
        print(r.stdout.strip() or "(empty rc=%s)" % r.returncode)
        if r.stderr.strip(): print("ERR:", r.stderr[:400])
    else:
        print("FAILED:", r)

show("service exec", "systemctl cat sba-autopilot.service | grep -E 'ExecStart|WorkingDirectory|EnvironmentFile' | head -5")
show("venv python?", "ls -la /home/ubuntu/sba-backend/venv/bin/python 2>/dev/null || ls -la /home/ubuntu/sba-backend/.venv/bin/python 2>/dev/null || echo 'no venv'")
show("venv import test", "cd /home/ubuntu/sba-backend && (venv/bin/python -c \"from admin.agency.sba_autopilot import _is_valid_lead_email; print('import OK via venv')\" 2>&1 || .venv/bin/python -c \"from admin.agency.sba_autopilot import _is_valid_lead_email; print('import OK via .venv')\" 2>&1) | tail -3")
