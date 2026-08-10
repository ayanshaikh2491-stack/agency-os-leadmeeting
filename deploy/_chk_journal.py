"""Remote: journal email_sent/enrich events + backfill log tail (timeout-safe)."""
import subprocess, sys, os, time
sys.path.insert(0, os.getcwd())
KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=45, tries=3):
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
        if r.stderr.strip(): print("ERR:", r.stderr[:300])
    else:
        print("FAILED:", r)

show("journal size", "wc -l /home/ubuntu/sba-backend/sba_reasoning_agency.log")
show("email_sent count", "grep -c email_sent /home/ubuntu/sba-backend/sba_reasoning_agency.log")
show("last 8 events", "tail -8 /home/ubuntu/sba-backend/sba_reasoning_agency.log")
show("backfill procs", "pgrep -af backfill | grep -v chrome | head -3; echo ---; ls /home/ubuntu/sba-backend/*.log | head -20")
show("enrich state", "python3 -c \"import json,time; d=json.load(open('/home/ubuntu/sba-backend/.sba_enrichment_state')); now=time.time(); fresh=[k for k,v in d.items() if now-v<2*3600]; print('total tracked:', len(d), 'tried in last 2h:', len(fresh))\"")
