import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=45):
    full = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=15",
            "-i", KEY, HOST, cmd]
    r = subprocess.run(full, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return r

cmds = [
    ("systemd env refs", r"grep -rh EnvironmentFile /etc/systemd/system/*.service 2>/dev/null; echo ---; ls -la /etc/systemd/system/*.service 2>/dev/null | head -30"),
    ("docker", "which docker; docker --version 2>&1; docker ps -a 2>&1 | head -20"),
    ("supabase", "ls -la /home/ubuntu/ 2>/dev/null; ls -la /home/ubuntu/supabase 2>/dev/null; ls -la /opt 2>/dev/null"),
    ("postgres", "which psql; systemctl list-units --type=service --state=running 2>/dev/null | grep -iE 'postgres|supabase|kong|gotrue|docker' "),
    ("key files", "ls -la /home/ubuntu/.env* 2>/dev/null; ls -la /etc/agency* 2>/dev/null; ls -la /home/ubuntu/agency-platform 2>/dev/null | head"),
]
for name, cmd in cmds:
    print(f"===== {name} =====")
    r = ssh(cmd)
    print(r.stdout[:4000])
    if r.stderr.strip():
        print("STDERR:", r.stderr[-1000:])
    print()
