"""One-shot live status: autopilot, backfill, DB counts, recent passes."""
import os, subprocess, sys, time, json
sys.path.insert(0, os.getcwd())

KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=90, tries=3):
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

def show(title, cmd):
    print(f"\n===== {title} =====")
    r = ssh(cmd)
    if isinstance(r, subprocess.CompletedProcess):
        out = (r.stdout or "").strip()
        print(out if out else "(no output) rc=%s" % r.returncode)
        if r.stderr and r.stderr.strip():
            print("STDERR:", r.stderr.strip()[:500])
    else:
        print("SSH FAILED:", r)

show("autopilot service", "systemctl is-active sba-autopilot.service; systemctl show sba-autopilot.service -p NRestarts,ActiveEnterTimestamp | head -3")
show("backfill proc", "pgrep -af backfill | head -5 || echo 'no backfill process'")
show("latest pass summary", "cd /home/ubuntu/sba-backend && tail -4 sba_reasoning_agency.log | python3 -c \"import sys,json; [print(json.loads(l).get('ts','')[:19], json.loads(l).get('event'), json.dumps(json.loads(l).get('stats',{}))[:220]) for l in sys.stdin if l.strip()]\" 2>/dev/null || tail -4 sba_reasoning_agency.log")
show("DB counts", "cd /home/ubuntu/sba-backend && python3 _db_counts_remote.py 2>&1")
show("enrichment state", "cd /home/ubuntu/sba-backend && python3 -c \"import json; d=json.load(open('.sba_enrichment_state')); print('tracked leads:', len(d.get('enriched_at', d) if isinstance(d,dict) else {}))\" 2>/dev/null || ls -la .sba_enrichment_state 2>/dev/null || echo 'no state file'")
