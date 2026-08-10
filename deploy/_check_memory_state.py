"""Check .env config + PB collections + whether agent memory is being written."""
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
                 "-o", "ConnectTimeout=20", "-i", KEY, HOST, cmd],
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
        print((r.stdout or "").strip()[:2500] or "(no output) rc=%s" % r.returncode)
        if r.stderr and r.stderr.strip():
            print("STDERR:", r.stderr.strip()[:300])
    else:
        print("SSH FAILED:", r)

# 1. Env config relevant to supabase/persistence
show(".env SUPABASE/GW keys", r'''cd /home/ubuntu/sba-backend && grep -E '^(SUPABASE|SERVICE_KEY|PB_|DATABASE)' .env | sed 's/=.*/=<hidden>/' ; echo '---URL values---'; grep -E '^(SUPABASE_URL|SERVICE_KEY|SUPABASE_SERVICE_KEY)=' .env | cut -d= -f2 | sed 's/\(.\{0,40\}\).*/\1.../' ''')

# 2. PB collections via PB admin API (127.0.0.1:8090)
show("PB collections (admin API)", r'''cd /home/ubuntu/sba-backend && python3 - <<'PYEOF'
import json, urllib.request
base="http://127.0.0.1:8090"
def post(path, body):
    req=urllib.request.Request(base+path, data=json.dumps(body).encode(), headers={"Content-Type":"application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=15) as r: return json.loads(r.read().decode())
try:
    auth=post("/api/collections/_superusers/auth-with-password", {"identity":"admin@tagsagency.local","password":"pb-admin-2026-x9"})
    tok=auth["token"]
    req=urllib.request.Request(base+"/api/collections?perPage=200", headers={"Authorization":"Bearer "+tok})
    with urllib.request.urlopen(req, timeout=15) as r: cols=json.loads(r.read().decode())
    names=[c["name"] for c in cols.get("items",[])]
    print("TOTAL:", len(names))
    for n in sorted(names): print(" -", n)
except Exception as e:
    print("ERR:", e)
PYEOF''')

# 3. Count agent_memory / checkpoints rows if collections exist
show("Memory row counts", r'''cd /home/ubuntu/sba-backend && python3 - <<'PYEOF'
import json, urllib.request, urllib.parse
base="http://127.0.0.1:8090"
def post(path, body):
    req=urllib.request.Request(base+path, data=json.dumps(body).encode(), headers={"Content-Type":"application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=15) as r: return json.loads(r.read().decode())
auth=post("/api/collections/_superusers/auth-with-password", {"identity":"admin@tagsagency.local","password":"pb-admin-2026-x9"})
tok=auth["token"]
for c in ["agent_memory","agent_messages","agent_data","agent_checkpoints","agent_checkpoint_writes"]:
    try:
        req=urllib.request.Request(base+f"/api/collections/{c}/records?perPage=1", headers={"Authorization":"Bearer "+tok})
        with urllib.request.urlopen(req, timeout=10) as r:
            d=json.loads(r.read().decode())
            print(f"{c}: {d.get('totalItems', 0)} rows")
    except Exception as e:
        print(f"{c}: MISSING ({e})")
PYEOF''')
