"""Diff EC2 sba_reason.py vs local to avoid clobbering other agents' changes."""
import os, subprocess, sys, hashlib
sys.path.insert(0, os.getcwd())

KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

local = open("admin/agency/sba_reason.py", "rb").read()
print("local sha256:", hashlib.sha256(local).hexdigest()[:16], "len", len(local))

r = subprocess.run(
    ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
     "-o", "ConnectTimeout=10", "-i", KEY, HOST,
     "cd /home/ubuntu/sba-backend && sha256sum admin/agency/sba_reason.py && md5sum admin/agency/sba_reason.py"],
    capture_output=True, text=True, timeout=60, encoding="utf-8", errors="replace")
print("EC2:", r.stdout[-400:])
print("rc:", r.returncode, r.stderr[-200:])
