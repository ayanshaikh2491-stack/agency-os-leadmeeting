"""Confirm latest autopilot pass + new leads in this pass."""
import os, subprocess, sys, time, json
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

r = ssh("cd /home/ubuntu/sba-backend && tail -20 sba_reasoning_agency.log")
if isinstance(r, subprocess.CompletedProcess):
    for line in r.stdout.strip().splitlines():
        try:
            d = json.loads(line)
            ev = d.get("event")
            ts = d.get("ts", "")[:19]
            if ev == "pass_summary":
                s = d.get("stats", {})
                print(f"{ts} pass_summary new_leads={s.get('new_leads_found')} total={s.get('new_leads_found',0)+s.get('deferred_to_business_hours',0)} no_email={s.get('no_email')}")
            else:
                print(f"{ts} {ev}", json.dumps(d)[:150])
        except Exception:
            print("RAW:", line[:150])
else:
    print("SSH FAILED:", r)
