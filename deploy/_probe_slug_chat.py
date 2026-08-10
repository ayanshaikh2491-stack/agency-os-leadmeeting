import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

script = r'''
echo "=== chat by slug ==="
curl -s -m 20 -X POST "http://127.0.0.1:8000/api/agents/seo-engine/chat" -H "Content-Type: application/json" -d '{"message":"status"}' | head -c 300
echo
echo "=== chat by slug ceo? ==="
curl -s -m 20 -X POST "http://127.0.0.1:8000/api/agents/ceo-agent/chat" -H "Content-Type: application/json" -d '{"message":"hi"}' | head -c 300
echo
echo "=== what slugs exist in code ==="
grep -rnE "'slug'|slug=" admin/api/routes/agent_aliases.py 2>/dev/null | head -5 || find . -name "agent_aliases.py" 2>/dev/null
echo "=== seo route ==="
curl -s -m 15 "http://127.0.0.1:8000/api/agents/seo-engine/status" | head -c 300
echo
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
