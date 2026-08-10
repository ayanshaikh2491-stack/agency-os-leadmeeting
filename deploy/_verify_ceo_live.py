import json
import sys

sys.path.insert(0, r"C:\Users\TAUSHEF\Downloads\int")

import subprocess

KEY = r"ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=40):
    r = subprocess.run(
        ["ssh", "-i", KEY, "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no",
         "-o", "ConnectTimeout=15", HOST, cmd],
        capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace",
    )
    return r

# 1. Check deployed ceo.py has get_checkpointer
r = ssh("grep -c 'get_checkpointer' /home/ubuntu/sba-backend/admin/agency/ceo.py")
print("ceo.py get_checkpointer refs:", (r.stdout or "").strip())

# 2. Check routes/ceo.py has conversation_id
r = ssh("grep -c 'conversation_id' /home/ubuntu/sba-backend/admin/api/routes/ceo.py")
print("routes/ceo.py conversation_id refs:", (r.stdout or "").strip())

# 3. Live API test: /api/ceo/chat with conversation_id (LLM call - may take time)
r = ssh(
    "curl -s -X POST http://localhost:8000/api/ceo/chat "
    "-H 'Content-Type: application/json' "
    "-d '{\"message\":\"Bhai, 1 line mein status batao\", \"conversation_id\":\"deploy-test-1\"}' "
    "-m 60",
    timeout=75,
)
out = (r.stdout or "").strip()
try:
    data = json.loads(out)
    print("chat response_id:", data.get("conversation_id"))
    print("agent_type:", data.get("agent_type"))
    resp = (data.get("response") or "")[:150]
    print("response:", resp)
except Exception:
    print("chat raw:", out[:300])

# 4. Health still ok
r = ssh("curl -s http://localhost:8000/api/health -m 10")
print("health:", (r.stdout or "").strip()[:120])
