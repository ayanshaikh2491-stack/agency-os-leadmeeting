"""Dig into why new_leads=0: check source rotation, scrape errors, chrome health."""
import os, subprocess, sys, time, json
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

# rotation / source related log lines
r = ssh("cd /home/ubuntu/sba-backend && grep -iE 'rotat|source|scrape|maps|yelp|throttl|block|captcha|error' sba_reasoning_agency.log | tail -15")
print("SOURCE/ROTATION LOG:")
print(r.stdout.strip()[-2000:] if r and r.stdout.strip() else "  none")

# chrome daemon health
r2 = ssh("systemctl is-active sba-chrome; echo ---; cd /home/ubuntu/sba-backend && grep -E 'new_lead|lead_found|inserted|created' sba_reasoning_agency.log | tail -8")
print("CHROME + LEAD EVENTS:")
print(r2.stdout.strip()[-1500:] if r2 and r2.stdout.strip() else "  none")
