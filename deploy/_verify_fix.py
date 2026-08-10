"""Verify: autopilot restarted cleanly + enrichment fix live + re-test beyondwow."""
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
        if r.stderr.strip(): print("ERR:", r.stderr[:300])
    else:
        print("FAILED:", r)

show("service", "systemctl is-active sba-autopilot.service; systemctl show sba-autopilot.service -p NRestarts,ActiveEnterTimestamp | head -3")
show("latest pass", "cd /home/ubuntu/sba-backend && tail -3 sba_reasoning_agency.log")
show("enrich fix live?", "cd /home/ubuntu/sba-backend && python3 -c \"from admin.tools.lead_enrichment import _is_valid_email; print('info@beyondwow.com verified:', _is_valid_email('info@beyondwow.com', allow_consumer=True)); print('info@beyondwow.com unverified:', _is_valid_email('info@beyondwow.com'))\"")
show("autopilot gate live?", "cd /home/ubuntu/sba-backend && python3 -c \"from admin.agency.sba_autopilot import _is_valid_lead_email; print('info@beyondwow.com verified:', _is_valid_lead_email('info@beyondwow.com', allow_consumer=True))\"")
show("beyondwow enrich", "cd /home/ubuntu/sba-backend && python3 -c \"from admin.tools.lead_enrichment import find_lead_email; import json; r=find_lead_email('Beyond Wow Plumbing & Drains','Austin','plumber','https://beyondwow.com/',patch_supabase=False); print(json.dumps({k:r[k] for k in ('email','provenance','domains')}))\"")
