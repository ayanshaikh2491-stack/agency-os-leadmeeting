"""Deploy stub-agent removal to EC2:
1. scp updated backend route files (agent_aliases.py, extra.py)
2. Compile check
3. Delete 4 stub agents from PocketBase 'agents' collection via gateway
4. Verify PB agents after deletion
5. Restart sba backend
"""
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

def scp(src, dst, timeout=90):
    r = subprocess.run(
        ["scp", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
         "-o", "ConnectTimeout=15", "-i", KEY, src, f"{HOST}:{dst}"],
        capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    print(f"scp {src} -> rc={r.returncode}")
    return r

# 1. Deploy backend route files
files = [
    ("admin/api/routes/agent_aliases.py", "/home/ubuntu/sba-backend/admin/api/routes/agent_aliases.py"),
    ("admin/api/routes/extra.py", "/home/ubuntu/sba-backend/admin/api/routes/extra.py"),
]
for src, dst in files:
    scp(src, dst)

# 2. Compile check on EC2
r = ssh("cd /home/ubuntu/sba-backend && python -m py_compile admin/api/routes/agent_aliases.py admin/api/routes/extra.py && echo COMPILE_OK")
print("compile:", (r.stdout or "").strip(), (r.stderr or "")[-200:] if getattr(r, "returncode", 1) else "")

# 3. Show current PB agents via gateway
r = ssh(r'''cd /home/ubuntu/sba-backend && GW_KEY=$(grep -E '^SUPABASE_SERVICE_KEY=' .env | sed 's/^SUPABASE_SERVICE_KEY=//' | tr -d '\r\n') && curl -s -m 10 -H "apikey: $GW_KEY" -H "Authorization: Bearer $GW_KEY" "http://127.0.0.1:8095/rest/v1/agents?select=id,name,slug&limit=100" | python3 -c "import sys,json; [print(' -', r.get('slug'), '|', r.get('name'), '|', r.get('id')) for r in json.load(sys.stdin)]"''')
print("PB agents BEFORE:")
print((r.stdout or "").strip() if isinstance(r, subprocess.CompletedProcess) else r)

# 4. Delete 4 stub agents
stub_slugs = ["intake-researcher", "sales-closer", "client-success", "review-qc"]
for slug in stub_slugs:
    r = ssh(r'''cd /home/ubuntu/sba-backend && GW_KEY=$(grep -E '^SUPABASE_SERVICE_KEY=' .env | sed 's/^SUPABASE_SERVICE_KEY=//' | tr -d '\r\n') && curl -s -m 10 -X DELETE -H "apikey: $GW_KEY" -H "Authorization: Bearer $GW_KEY" -H "Prefer: return=minimal" "http://127.0.0.1:8095/rest/v1/agents?slug=eq.%s" | head -c 200; echo " <- delete %s"''' % (slug, slug))
    print("delete %s: %s" % (slug, (r.stdout or "").strip()[:200] if isinstance(r, subprocess.CompletedProcess) else r))

# 5. Verify PB agents after deletion
r = ssh(r'''cd /home/ubuntu/sba-backend && GW_KEY=$(grep -E '^SUPABASE_SERVICE_KEY=' .env | sed 's/^SUPABASE_SERVICE_KEY=//' | tr -d '\r\n') && curl -s -m 10 -H "apikey: $GW_KEY" -H "Authorization: Bearer $GW_KEY" "http://127.0.0.1:8095/rest/v1/agents?select=id,name,slug&limit=100" | python3 -c "import sys,json; [print(' -', r.get('slug'), '|', r.get('name'), '|', r.get('id')) for r in json.load(sys.stdin)]"''')
print("PB agents AFTER:")
print((r.stdout or "").strip() if isinstance(r, subprocess.CompletedProcess) else r)

# 6. Restart sba backend so route changes take effect
r = ssh("sudo -n systemctl restart sba && sleep 3 && systemctl is-active sba.service && curl -s -m 10 http://127.0.0.1:8000/api/health | head -c 200")
print("restart sba:", (r.stdout or "").strip()[:300] if isinstance(r, subprocess.CompletedProcess) else r)
