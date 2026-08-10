"""Audit ALL emails patched by backfill today + flag junk candidates."""
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

# all EMAIL lines from log
r = ssh("grep -E '^[0-9:]+ EMAIL' /tmp/backfill.log")
print("=== BACKFILL EMAIL PATCHES ===")
print(r.stdout[-5000:])
