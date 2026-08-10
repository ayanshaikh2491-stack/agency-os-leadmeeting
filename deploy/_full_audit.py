"""Full agency system audit: langgraph agents, API routes, scheduler, stores."""
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

# 1. LangGraph agents present + importable
show("langgraph agents import", "cd /home/ubuntu/sba-backend && venv/bin/python - <<'PYEOF' 2>&1 | head -30\nimport sys; sys.path.insert(0,'.')\nimport importlib\nfor m in ['admin.agency.ceo','admin.agency.langgraph_sba','admin.agency.content_agent','admin.agency.orchestrator']:\n    try:\n        mod=importlib.import_module(m)\n        cls=[n for n,v in vars(mod).items() if isinstance(v,type) and ('Agent' in n or 'CEO' in n or 'Graph' in n)]\n        print(m, '->', cls)\n    except Exception as e:\n        print(m, 'FAIL:', str(e)[:120])\nPYEOF")
# 2. AgencyCEO graph built OK?
show("AgencyCEO graph build", "cd /home/ubuntu/sba-backend && venv/bin/python - <<'PYEOF' 2>&1 | head -10\nimport sys; sys.path.insert(0,'.')\nfrom admin.agency.ceo import AgencyCEO\ntry:\n    c=AgencyCEO()\n    print('graph nodes:', list(c.graph.get_graph().nodes.keys()) if hasattr(c.graph,'get_graph') else 'n/a')\nexcept Exception as e:\n    print('FAIL:', str(e)[:300])\nPYEOF")
# 3. API routes exposed by agents
show("agent API routes", "cd /home/ubuntu/sba-backend && venv/bin/python - <<'PYEOF' 2>&1 | head -60\nimport sys; sys.path.insert(0,'.')\nfrom admin.main import app\npaths=set()\nfor r in app.routes:\n    p=getattr(r,'path',None)\n    if p: paths.add(p)\nfor p in sorted(paths):\n    if any(k in p.lower() for k in ['/agents','/ceo','/content','/seo','/social','/website','/ads','/swarm','/orchestrator','/sba','/workspace']):\n        print(p)\nPYEOF")
# 4. Scheduler — koi daemon baaki agents chala raha hai?
show("scheduler service/proc", "systemctl list-units --type=service --no-legend | grep -iE 'sched|content|seo|social|website|ads|ceo' || echo 'no agent services'; echo '---'; pgrep -af 'scheduler|content_agent|ceo.py' | grep -v grep | head -10 || echo 'no agent processes'")
# 5. SBA autopilot pass (latest)
show("latest pass", "cd /home/ubuntu/sba-backend && tail -3 sba_reasoning_agency.log 2>/dev/null | python3 -c \"import sys,json\nfor l in sys.stdin:\n l=l.strip()\n if not l: continue\n try:\n  d=json.loads(l); print(d.get('ts','')[:19], d.get('event'), json.dumps(d.get('stats',{}))[:200])\n except: print(l[:160])\" 2>/dev/null || echo 'no log'")
# 6. Workspace agent stores
show("workspace stores", "ls /home/ubuntu/sba-backend/data/ 2>/dev/null; echo '---'; ls /home/ubuntu/sba-backend/data/workspace_content_agents/ 2>/dev/null | head -5; echo '---'; ls /home/ubuntu/sba-backend/data/social_tokens/ 2>/dev/null | head -5")
