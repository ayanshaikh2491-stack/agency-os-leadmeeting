#!/usr/bin/env python3
"""Run a local bash script on EC2: scp -> execute.
Usage: python _run_script.py deploy/script.sh [extra remote args...]
"""
import os
import subprocess
import sys

KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"
script = sys.argv[1]
extra = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
remote_name = os.path.basename(script)


def run(args, timeout=120):
    r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    print(r.stdout)
    if r.stderr:
        print("STDERR:", r.stderr[:4000])
    print("rc=", r.returncode)
    return r


run(["scp", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
     "-o", "ConnectTimeout=15", "-i", KEY, script,
     f"{HOST}:/home/ubuntu/{remote_name}"], 60)
cmd = f"bash /home/ubuntu/{remote_name} {extra}"
run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
     "-o", "ConnectTimeout=15", "-o", "ServerAliveInterval=5",
     "-o", "ServerAliveCountMax=2", "-i", KEY, HOST, cmd])
