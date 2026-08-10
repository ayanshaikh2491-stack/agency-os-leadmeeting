import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

cmds = [
    "echo CONN_OK; hostname; uptime",
    "systemctl list-units --type=service --state=running | grep -iE 'sba|pocket|gateway|pb' || echo NO_SBA_SERVICES",
    "ss -tlnp | grep -E ':(8000|8090|8095|8050)' || echo NO_LISTEN",
    "ps aux | grep -iE 'pocketbase|pb_gateway' | grep -v grep || echo NO_PB_PROCS",
    "ls -la /home/ubuntu/sba-backend/deploy/ 2>/dev/null | head -30",
    "tail -30 /home/ubuntu/sba-backend/deploy/pocketbase/pb_serve.log 2>/dev/null || echo NO_PB_LOG",
    "cat /home/ubuntu/sba-backend/.env 2>/dev/null | grep -iE 'SUPABASE|POCKET|GATEWAY|8050|8095|8090' || echo NO_ENV_MATCH",
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
        print("ERR:", r.stderr.strip()[:500])
    except Exception as e:
        print("EXC:", e)
