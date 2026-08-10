import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

cmds = [
    # Backend .env: what does it point to?
    "grep -E 'SUPABASE|PB_|GATEWAY' /home/ubuntu/sba-backend/.env | sed 's/=.*KEY.*/=[REDACTED]/' | head -20",
    # How does backend call supabase? find the client setup
    "grep -rn 'Content-Profile\\|content-profile' /home/ubuntu/sba-backend --include='*.py' | grep -v venv | grep -v pb_gateway | head -20",
    "grep -rn 'SUPABASE_URL\\|supabase' /home/ubuntu/sba-backend/app --include='*.py' | grep -v venv | head -20",
    # is there an import script on EC2?
    "ls -la /home/ubuntu/sba-backend/*.py | head -30",
]

for cmd in cmds:
    print("=" * 20)
    print("CMD:", cmd[:120])
    try:
        r = subprocess.run(
            ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
             "-o", "ConnectTimeout=10", "-i", KEY, HOST, cmd],
            capture_output=True, text=True, timeout=40, encoding="utf-8", errors="replace",
        )
        print("RC:", r.returncode)
        print("OUT:", r.stdout.strip()[:3000])
        print("ERR:", r.stderr.strip()[:500])
    except Exception as e:
        print("EXC:", e)
