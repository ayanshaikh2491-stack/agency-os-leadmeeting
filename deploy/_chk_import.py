"""Verify backfill imports cleanly (no circular import) on EC2."""
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

r = ssh("cd /home/ubuntu/sba-backend && venv/bin/python -c \"import ast; ast.parse(open('_backfill_websites.py').read()); print('SYNTAX_OK')\"")
print("syntax:", r.stdout.strip()[-40:], r.returncode)

# import test (catches circular import at runtime)
r = ssh("cd /home/ubuntu/sba-backend && venv/bin/python -c \"import _backfill_websites; print('IMPORT_OK')\"", timeout=60)
print("import:", r.stdout.strip()[-60:], r.returncode, r.stderr[-300:])
