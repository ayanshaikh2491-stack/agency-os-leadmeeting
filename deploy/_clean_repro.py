"""Clean repro.test rows + count website progress + check autopilot log window."""
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

# cleanup repro.test rows
r = ssh("cd /home/ubuntu/sba-backend && venv/bin/python - <<'EOF'\n"
        "import json, urllib.request, urllib.error\n"
        "from admin.agency import sba_pipeline as pipe\n"
        "url, key = pipe.supabase_config()\n"
        "headers = {'apikey': key, 'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'}\n"
        "rows = pipe.sb_request(url, key, '/rest/v1/leads?select=id,website&website=like.*repro.test*')\n"
        "print('repro rows:', rows)\n"
        "for row in rows or []:\n"
        "    sid = str(row.get('id'))\n"
        "    req = urllib.request.Request(f'{url}/rest/v1/leads?id=eq.{sid}', data=json.dumps({'website': None, 'has_website': False, 'website_status': 'verified_none'}).encode(), headers=headers, method='PATCH')\n"
        "    try:\n"
        "        with urllib.request.urlopen(req, timeout=20) as resp:\n"
        "            print('clean', sid, resp.status)\n"
        "    except urllib.error.HTTPError as e:\n"
        "        print('clean', sid, e.code, e.read().decode()[:200])\n"
        "w = pipe.sb_request(url, key, '/rest/v1/leads?select=website&website=not.is.null')\n"
        "ws = [x for x in w or [] if x.get('website')]\n"
        "print('rows with website:', len(ws))\n"
        "for x in ws[:15]:\n"
        "    print('  ', x.get('website'))\n"
        "EOF")
print(r.stdout[-3000:])
print("rc:", r.returncode, r.stderr[-300:])
