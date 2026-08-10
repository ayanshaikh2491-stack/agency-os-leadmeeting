import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

script = r'''
echo "=== /api/agents ==="
curl -s -m 15 http://127.0.0.1:8000/api/agents | python3 -c "import sys,json; d=json.load(sys.stdin); print(type(d).__name__, len(d) if isinstance(d,list) else d)" 2>&1 | head -3
echo "=== /api/status ==="
curl -s -m 15 http://127.0.0.1:8000/api/status | python3 -c "import sys,json; d=json.load(sys.stdin); print(list(d.keys())[:20])" 2>&1 | head -3
echo "=== agent aliases routes on disk ==="
grep -nE "router\.(get|post)|APIRouter" admin/api/routes/agent_aliases.py | head -20
echo "=== probe each agent chat quickly (timeout 10s each) ==="
for a in "CEO Agent" "SEO Engine" "Content Creator" "Analytics Bot"; do
  echo "-- $a --"
  curl -s -m 10 -X POST "http://127.0.0.1:8000/api/agents/$a/chat" -H "Content-Type: application/json" -d '{"message":"hi"}' | head -c 200
  echo
done
echo "=== backend errors last 2h ==="
sudo journalctl -u sba.service --since '2026-08-09 16:15:00' --no-pager | grep -iE "error|traceback|exception|failed" | tail -8
'''

r = subprocess.run(
    ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-i", KEY, HOST, script],
    capture_output=True, text=True, timeout=180,
)
print(r.stdout)
if r.stderr:
    print("STDERR:", r.stderr[:1000])
print("rc=", r.returncode)
