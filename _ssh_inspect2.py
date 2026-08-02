import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=40):
    full = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=15",
            "-i", KEY, HOST, cmd]
    r = subprocess.run(full, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return r

cmds = [
    ("backend .env exists", "ls -la /home/ubuntu/agency-platform/backend/.env 2>&1; echo ---; ls /home/ubuntu/agency-platform/backend 2>&1 | head -20"),
    ("supabase dirs", "find /home/ubuntu -maxdepth 2 -iname '*supabase*' 2>/dev/null; echo ---; ls /home/ubuntu/agency-platform 2>&1 | head -20"),
    ("docker compose files", "find /home/ubuntu -maxdepth 3 -name 'docker-compose*.yml' -o -maxdepth 3 -name 'docker-compose*.yaml' 2>/dev/null | head"),
    ("swap & memory", "free -m; echo ---; swapon --show 2>&1"),
    ("port 5432 & supabase ports", "ss -tlnp 2>/dev/null | grep -E ':(5432|8000|8080|54321|54322|8001|3000|4000|9000|9001)' "),
]
for name, cmd in cmds:
    print(f"===== {name} =====")
    r = ssh(cmd, timeout=40)
    print(r.stdout[:3500])
    if r.stderr.strip():
        print("STDERR:", r.stderr[-800:])
    print()
