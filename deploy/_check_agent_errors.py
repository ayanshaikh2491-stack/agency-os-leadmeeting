import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

script = r'''
cd /home/ubuntu/sba-backend
echo "=== ceo.py classes ==="
grep -nE "^class |^def get_ceo|^def build" admin/agency/ceo.py | head -20
echo "=== agents routes ==="
grep -rnE "@router|@app\.(get|post)" routes/agent_aliases.py 2>/dev/null | head -30
echo "=== agent alias chat probe ==="
curl -s -m 10 -X POST http://127.0.0.1:8000/api/agents/CEO\ Agent/chat -H "Content-Type: application/json" -d '{"message":"status?"}' | head -c 400
echo
echo "=== backend recent errors ==="
sudo journalctl -u sba.service --since '2026-08-09 16:00:00' --no-pager | grep -iE "error|traceback|exception" | tail -10
echo "=== done ==="
'''

r = subprocess.run(
    ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-i", KEY, HOST, script],
    capture_output=True, text=True, timeout=120,
)
print(r.stdout)
if r.stderr:
    print("STDERR:", r.stderr[:1000])
print("rc=", r.returncode)
