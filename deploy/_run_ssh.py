#!/usr/bin/env python3
"""Run a remote command on EC2 via SSH (avoids cmd.exe quoting issues).
Usage: python _run_ssh.py echo SSH_OK && uptime
All args are joined with spaces into one remote command.
"""
import os
import subprocess
import sys

KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"
cmd = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "echo SSH_OK"


def run(args, timeout=60):
    r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    print(r.stdout)
    if r.stderr:
        print("STDERR:", r.stderr[:2000])
    print("rc=", r.returncode)
    return r


run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
     "-o", "ConnectTimeout=15", "-o", "ServerAliveInterval=5",
     "-o", "ServerAliveCountMax=2", "-i", KEY, HOST, cmd])
