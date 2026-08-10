import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

cmds = [
    "ss -tlnp | grep 8050",
    "curl -sf http://127.0.0.1:8050/health 2>/dev/null || echo NO_8050_HEALTH",
    "curl -sf http://127.0.0.1:8050/api/health 2>/dev/null || echo NO_8050_API_HEALTH",
    "curl -sf http://127.0.0.1:8095/api/health 2>/dev/null || echo NO_8095_HEALTH",
    "curl -sf http://127.0.0.1:8090/api/health 2>/dev/null || echo NO_8090_HEALTH",
    "cat /home/ubuntu/sba-backend/pb_gw.log 2>/dev/null | tail -40 || echo NO_GW_LOG",
]

for cmd in cmds:
    print("=" * 20)
    print("CMD:", cmd)
    try:
        r = subprocess.run(
            ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
             "-o", "ConnectTimeout=10", "-i", KEY, HOST, cmd],
            capture_output=True, text=True, timeout=25, encoding="utf-8", errors="replace",
        )
        print("RC:", r.returncode)
        print("OUT:", r.stdout.strip()[:1500])
        print("ERR:", r.stderr.strip()[:300])
    except Exception as e:
        print("EXC:", e)
