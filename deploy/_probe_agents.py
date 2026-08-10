"""Focused probe: CEO attrs, API routes, reply event, other agent stores."""
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

# Fix route introspection: handle _IncludedRouter by reading app.routes attributes safely
show("API routes (agent-related)", "cd /home/ubuntu/sba-backend && venv/bin/python - <<'EOF' 2>&1 | head -50\nimport sys; sys.path.insert(0,'.')\nfrom admin.main import app\npaths=set()\nfor r in app.routes:\n    try:\n        p=getattr(r,'path',None)\n        if p: paths.add(p)\n    except Exception:\n        pass\nfor p in sorted(paths):\n    if any(k in p.lower() for k in ['agent','ceo','content','seo','social','website','ads','swarm','orchestrator','sba']):\n        print(p)\nEOF")
show("AgencyCEO attrs", "cd /home/ubuntu/sba-backend && venv/bin/python - <<'EOF' 2>&1 | head -20\nimport sys; sys.path.insert(0,'.')\nfrom admin.agency.ceo import AgencyCEO\nc=AgencyCEO()\nprint('dir sample:', [a for a in dir(c) if not a.startswith('_')][:30])\nEOF")
show("reply_understood detail", "cd /home/ubuntu/sba-backend && grep -a 'reply' sba_reasoning_agency.log 2>/dev/null | tail -3 | python3 -c \"import sys,json;\nfor l in sys.stdin:\n l=l.strip()\n if not l: continue\n try:\n  d=json.loads(l); print(d.get('ts','')[:19], d.get('event'), json.dumps(d)[:400])\n except Exception: print(l[:300])\" 2>/dev/null || grep -a 'reply' sba_reasoning_agency.log | tail -3")
show("workspace content agents", "ls -la /home/ubuntu/sba-backend/data/workspace_content_agents/ 2>/dev/null | head; echo '---'; cat /home/ubuntu/sba-backend/data/workspace_content_agents/*.json 2>/dev/null | head -40 || echo 'no json'")
show("social tokens", "ls -la /home/ubuntu/sba-backend/data/social_tokens/ 2>/dev/null | head -10")
show("content store state", "cd /home/ubuntu/sba-backend && venv/bin/python -c \"import sys; sys.path.insert(0,'.'); from admin.workspace.content_store import ContentStore; s=ContentStore(); print('rows:', len(s.list_all()) if hasattr(s,'list_all') else 'n/a')\" 2>&1 | head -5")
