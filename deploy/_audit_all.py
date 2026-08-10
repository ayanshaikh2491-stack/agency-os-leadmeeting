"""Comprehensive live audit of ALL agency agents on EC2."""
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
            print("STDERR:", r.stderr.strip()[:400])
    else:
        print("SSH FAILED:", r)

show("services", "systemctl list-units --type=service --no-legend | grep -iE 'sba|ceo|agent' || echo none")
show("sba-chrome status", "systemctl status sba-chrome.service --no-pager -l 2>&1 | head -12")
show("API routes (agents exposed)", "cd /home/ubuntu/sba-backend && venv/bin/python -c \"import sys; sys.path.insert(0,'.'); from admin.main import app; routes=[r.path for r in app.routes]; print(chr(10).join(sorted(set(x for x in routes if any(k in x.lower() for k in ['agent','ceo','content','seo','social','website','ads','swarm','orchestrator','sba'])))[:60]))\" 2>&1 | head -60")
show("AgencyCEO status", "cd /home/ubuntu/sba-backend && venv/bin/python -c \"import sys; sys.path.insert(0,'.'); from admin.agency.ceo import AgencyCEO; c=AgencyCEO(); print('ready:', getattr(c,'ready',None), 'workspaces:', getattr(c,'workspaces',None) or getattr(c,'_workspaces',None) or 'n/a')\" 2>&1 | head -6")
show("email sends today (journal)", "journalctl -u sba-autopilot.service --since 'today' --no-pager 2>/dev/null | grep -iE 'email.*sent|sent.*email|send.*success|emails_sent' | tail -15")
show("reply handling", "journalctl -u sba-autopilot.service --since 'today' --no-pager 2>/dev/null | grep -iE 'reply|reply_understood' | tail -10")
show("content agent store", "ls -la /home/ubuntu/sba-backend/admin/data/ 2>/dev/null | head -20; echo '---'; find /home/ubuntu/sba-backend -maxdepth 3 -name '*content*' -o -name '*seo*' -o -name '*social*' 2>/dev/null | grep -v __pycache__ | head -20")
