"""Live audit of ALL agency agents on EC2: services, agents, API, organic engine."""
import os, subprocess, sys, time
sys.path.insert(0, os.getcwd())
KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=90, tries=2):
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
    print(f"\n===== {title} =====")
    r = ssh(cmd)
    if isinstance(r, subprocess.CompletedProcess):
        out = (r.stdout or "").strip()
        print(out if out else "(no output) rc=%s" % r.returncode)
        if r.stderr and r.stderr.strip():
            print("STDERR:", r.stderr.strip()[:300])
    else:
        print("SSH FAILED:", r)

show("ALL systemd services (agency-related)",
     "systemctl list-units --type=service --all --no-legend | grep -iE 'sba|ceo|agent|organic|content|seo|social|website|ads' || echo 'none matched'")
show("Running processes (agents)",
     "ps aux | grep -iE 'python|node' | grep -viE 'grep|systemd|chrome|chromium' | head -25")
show("API health",
     "curl -s http://localhost:8050/api/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8050/api/health")
show("CEO agent status",
     "cd /home/ubuntu/sba-backend && venv/bin/python -c \"import sys; sys.path.insert(0,'.'); from admin.agency.ceo import CEOAgent; c=CEOAgent(); print('CEO ready:', getattr(c,'ready',getattr(c,'status','unknown')))\" 2>&1 | head -5")
show("Organic engine channels",
     "cd /home/ubuntu/sba-backend && ls admin/organic_config/ 2>/dev/null; echo '---'; cat admin/organic_config/*.json 2>/dev/null | head -30 || echo 'no config'")
show("Recent autopilot passes (last 8)",
     "cd /home/ubuntu/sba-backend && tail -8 sba_reasoning_agency.log 2>/dev/null | python3 -c \"import sys,json;\nfor l in sys.stdin:\n l=l.strip()\n if not l: continue\n try:\n  d=json.loads(l); print(d.get('ts','')[:19], d.get('event'), json.dumps(d.get('stats',{}))[:180])\n except Exception: print(l[:180])\" 2>/dev/null || tail -8 sba_reasoning_agency.log 2>/dev/null || echo 'no log'")
