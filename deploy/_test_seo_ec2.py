"""Test SEO agent directly on EC2 to capture the real exception."""
import os, subprocess, sys
sys.path.insert(0, os.getcwd())

KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=120, tries=2):
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
import asyncio, traceback, logging
logging.basicConfig(level=logging.WARNING)
from admin.workspace.agents.seo import SEOAgent
async def main():
    try:
        a = SEOAgent(workspace_name="Agency Workspace", client_name="TAGS Agency")
        print("checkpointer type:", type(a.graph.checkpointer).__name__ if hasattr(a.graph,'checkpointer') else "none")
        resp, tid = await a.chat("Hello, introduce yourself briefly")
        print("RESP:", resp[:200])
        print("TID:", tid)
    except Exception:
        traceback.print_exc()
asyncio.run(main())
PYEOF''')
print((r.stdout or "")[-3000:])
if r.stderr and r.stderr.strip():
    print("STDERR:", r.stderr[-800:])
