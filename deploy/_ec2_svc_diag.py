import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

cmds = [
    # Where is SUPABASE_URL consumed in backend code?
    "grep -rn 'SUPABASE_URL' /home/ubuntu/sba-backend --include='*.py' | grep -v venv | grep -v '~\\\\.' | head -10",
    # Service units for gateway / backend
    "systemctl list-units --type=service --no-pager | grep -iE 'sba|gateway|pb|supabase|back' | head -20",
    "systemctl cat sba-autopilot.service 2>/dev/null | head -30",
    # Gateway started how? check parent
    "ps -o pid,ppid,lstart,cmd -p 3828032",
    # Docker compose for supabase (to stop later)
    "docker ps --format '{{.Names}} {{.Ports}}' 2>/dev/null | head -20",
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
