#!/usr/bin/env python3
"""Debug SSH connection: verbose output, short timeout."""
import os
import subprocess
import sys

KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"
cmd = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "echo SSH_OK"

r = subprocess.run(
    ["ssh", "-v", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
     "-o", "ConnectTimeout=15", "-o", "ServerAliveInterval=5",
     "-o", "ServerAliveCountMax=2", "-i", KEY, HOST, cmd],
    capture_output=True, text=True, timeout=90)
print("STDOUT:", r.stdout[-3000:])
print("STDERR:", r.stderr[-4000:])
print("rc=", r.returncode)
