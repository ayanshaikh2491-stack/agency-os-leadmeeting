"""Autopilot log tail + DB counts (websites, emails)."""
import os, subprocess, sys
sys.path.insert(0, os.getcwd())

KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=45):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
         "-o", "ConnectTimeout=10", "-i", KEY, HOST, cmd],
        capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return r

r = ssh("tail -40 /home/ubuntu/sba-backend/sba_reasoning_agency.log; echo ===COUNTS===; "
        "cd /home/ubuntu/sba-backend && venv/bin/python - <<'EOF'\n"
        "from admin.agency import sba_pipeline as pipe\n"
        "url, key = pipe.supabase_config()\n"
        "all_rows = pipe.sb_request(url, key, '/rest/v1/leads?select=id,website,email,website_status,email_provenance')\n"
        "n = len(all_rows or [])\n"
        "ws = sum(1 for r in all_rows or [] if r.get('website'))\n"
        "em = sum(1 for r in all_rows or [] if r.get('email'))\n"
        "ws_noem = sum(1 for r in all_rows or [] if r.get('website') and not r.get('email'))\n"
        "prov = {}\n"
        "for r in all_rows or []:\n"
        "    p = r.get('email_provenance') or 'none'\n"
        "    prov[p] = prov.get(p, 0) + 1\n"
        "print('total', n, '| website', ws, '| email', em, '| website+no-email', ws_noem)\n"
        "print('provenance:', prov)\n"
        "EOF")
print(r.stdout[-5000:])
print("rc:", r.returncode, r.stderr[-300:])
