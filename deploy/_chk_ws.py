"""Check agency workspace config: sourcing enabled? rotation? Also count leads in DB."""
import os, subprocess, sys, time, json
sys.path.insert(0, os.getcwd())

KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=60, tries=3):
    for i in range(tries):
        try:
            r = subprocess.run(
                ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
                 "-o", "ConnectTimeout=10", "-i", KEY, HOST, cmd],
                capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
            if r.returncode == 0 or r.stdout.strip():
                return r
        except Exception:
            pass
        time.sleep(3)
    return None

# workspace config
r = ssh("cd /home/ubuntu/sba-backend && venv/bin/python -c \"from admin.agency.sba_biztypes import get_workspace_config, list_sba_workspaces; ws=list_sba_workspaces(); print(ws); import json; print(json.dumps(get_workspace_config('agency'), default=str)[:800])\"")
print("WORKSPACE CONFIG:")
print(r.stdout.strip()[-1500:] if r and r.stdout.strip() else "  none / " + (r.stderr[-200:] if r else "SSH_FAIL"))

# DB lead counts by source
r2 = ssh("cd /home/ubuntu/sba-backend && venv/bin/python -c \"from admin.agency.sba_pipeline import supabase_config, load_leads; u,k=supabase_config(); ls=load_leads(u,k); print('total', len(ls)); from collections import Counter; print(Counter((l.get('source') or 'unknown') for l in ls))\"")
print("DB SOURCES:")
print(r2.stdout.strip()[-800:] if r2 and r2.stdout.strip() else "  none / " + (r2.stderr[-300:] if r2 else "SSH_FAIL"))
