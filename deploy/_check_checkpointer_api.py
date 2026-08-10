"""Inspect BaseCheckpointSaver API in langgraph-checkpoint 4.1.1."""
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
                 "-o", "ConnectTimeout=20", "-i", KEY, HOST, cmd],
                capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
            if r.returncode == 0 or r.stdout.strip():
                return r
            last = r
        except Exception as e:
            last = e
        time.sleep(3)
    return last

r = ssh(r'''cd /home/ubuntu/sba-backend && venv/bin/python - <<'PYEOF'
import inspect
from langgraph.checkpoint.base import BaseCheckpointSaver
print("abstract methods:", BaseCheckpointSaver.__abstractmethods__)
src = inspect.getsource(BaseCheckpointSaver.put)
print("--- put signature ---")
print(inspect.signature(BaseCheckpointSaver.put))
print(inspect.getsource(BaseCheckpointSaver.put)[:1200])
print("--- put_writes ---")
print(inspect.signature(BaseCheckpointSaver.put_writes))
print("--- get_tuple ---")
print(inspect.signature(BaseCheckpointSaver.get_tuple))
print("--- list ---")
print(inspect.signature(BaseCheckpointSaver.list))
PYEOF''')
print((r.stdout or "")[:4000])
if r.stderr and r.stderr.strip():
    print("STDERR:", r.stderr[-600:])
