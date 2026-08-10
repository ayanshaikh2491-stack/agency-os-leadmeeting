"""Inspect BaseCheckpointSaver API in langgraph-checkpoint 4.1.1 (v2)."""
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
print("MRO:", [c.__name__ for c in BaseCheckpointSaver.__mro__])
for name in ["put", "aput", "put_writes", "aput_writes", "get_tuple", "aget_tuple", "list", "alist"]:
    fn = getattr(BaseCheckpointSaver, name, None)
    if fn is None:
        print(name, ": MISSING")
        continue
    try:
        print(name, inspect.signature(fn))
    except Exception as e:
        print(name, "sig err", e)
print("--- put source ---")
try:
    print(inspect.getsource(BaseCheckpointSaver.put)[:1500])
except Exception as e:
    print("no put source:", e)
PYEOF''')
print((r.stdout or "")[:4000])
if r.stderr and r.stderr.strip():
    print("STDERR:", r.stderr[-600:])
