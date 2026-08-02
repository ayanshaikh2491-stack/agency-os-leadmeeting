import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=30):
    full = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=12",
            "-i", KEY, HOST, cmd]
    r = subprocess.run(full, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return r

cmds = [
    ("agency-platform exists", "test -d /home/ubuntu/agency-platform && echo YES || echo NO; test -d /home/ubuntu/agency-platform/backend && echo BACKEND_YES || echo BACKEND_NO"),
    ("find main.py (bounded)", "timeout 12 find /opt /srv /var/www /home/ubuntu -maxdepth 3 -name 'main.py' -not -path '*/node_modules/*' 2>/dev/null | head"),
    ("docker compose supabase", "timeout 12 find /home/ubuntu /opt /srv -maxdepth 3 -name 'docker-compose*' 2>/dev/null | head; echo ---; ls /home/ubuntu/agency-platform 2>&1 | head -30"),
    ("service file contents", "cat /etc/systemd/system/agency-backend.service; echo =====; cat /etc/systemd/system/sba-agent.service"),
]
for name, cmd in cmds:
    print(f"===== {name} =====")
    r = ssh(cmd, timeout=35)
    print(r.stdout[:3500])
    if r.stderr.strip():
        print("STDERR:", r.stderr[-800:])
    print()
