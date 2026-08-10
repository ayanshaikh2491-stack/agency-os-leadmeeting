"""Check langgraph version + available checkpoint.base symbols."""
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
import langgraph
print("langgraph:", langgraph.__version__)
import langgraph.checkpoint.base as b
print("has empty_checkpoint_id:", hasattr(b, "empty_checkpoint_id"))
print("has uuid_type:", hasattr(b, "uuid_type"))
print("has empty_channel:", hasattr(b, "empty_channel"))
print("symbols:", [x for x in dir(b) if not x.startswith("_")][:40])
PYEOF''')
print((r.stdout or "")[:2000])
if r.stderr and r.stderr.strip():
    print("STDERR:", r.stderr[-500:])
