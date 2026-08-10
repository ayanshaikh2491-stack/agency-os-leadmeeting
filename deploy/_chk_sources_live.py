"""Check which lead sources actually return leads on EC2 (per-pass log lines)."""
import os, subprocess, sys, time
sys.path.insert(0, os.getcwd())

KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=90, tries=4):
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
        time.sleep(5)
    return last

# Look for source->N leads lines in journal and python logs
r = ssh("cd /home/ubuntu/sba-backend && journalctl -u sba-autopilot --since '1 hour ago' --no-pager 2>/dev/null | grep -E 'source .* ->|lead rotation|find_leads' | tail -25")
print("JOURNAL SOURCE LINES:")
print(r.stdout.strip()[-2500:] if r and r.stdout.strip() else "  none")
if not (r and r.stdout.strip()):
    r2 = ssh("cd /home/ubuntu/sba-backend && grep -aE 'source .* ->|lead rotation' *.log 2>/dev/null | tail -25")
    print("LOG FILES:")
    print(r2.stdout.strip()[-2500:] if r2 and r2.stdout.strip() else "  none")
