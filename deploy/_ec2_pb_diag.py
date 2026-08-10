import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

cmds = [
    # What is on 8050?
    "sudo lsof -i :8050 2>/dev/null || ss -tlnp | grep 8050",
    "ps aux | grep -E '8050|supabase|kong' | grep -v grep | head",
    # Find gateway traceback in journald or nohup
    "ls -la /home/ubuntu/sba-backend/pb_gw.log /home/ubuntu/pb_gw.log 2>/dev/null",
    "grep -n 'Traceback\\|Error\\|Exception' /home/ubuntu/sba-backend/pb_gw.log 2>/dev/null | tail -20 || echo NO_TRACEBACK",
    # Reproduce a POST and capture body
    "curl -s -X POST http://127.0.0.1:8095/rest/v1/leads -H 'apikey: test' -H 'Authorization: Bearer test' -H 'Content-Type: application/json' -H 'Content-Profile: leads' -d '{\"name\":\"probe-test\"}' | head -c 500",
    "echo ''",
    # Check if the 500s correlate with backend restart (when did they happen)
    "journalctl -u sba.service --since '2 hours ago' --no-pager 2>/dev/null | grep -iE 'error|traceback' | tail -20 || echo NO_SBA_ERRORS",
]

for cmd in cmds:
    print("=" * 20)
    print("CMD:", cmd)
    try:
        r = subprocess.run(
            ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
             "-o", "ConnectTimeout=10", "-i", KEY, HOST, cmd],
            capture_output=True, text=True, timeout=30, encoding="utf-8", errors="replace",
        )
        print("RC:", r.returncode)
        print("OUT:", r.stdout.strip()[:2000])
        print("ERR:", r.stderr.strip()[:300])
    except Exception as e:
        print("EXC:", e)
