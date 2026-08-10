import subprocess, os

os.chdir(r"C:\Users\TAUSHEF\Downloads\int")
KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=120):
    print(">>>", cmd)
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
                        "-o", "ConnectTimeout=10", "-i", KEY, HOST, cmd],
                       capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    print("rc=", r.returncode)
    print(r.stdout.strip()[:4000])
    if r.stderr.strip():
        print("ERR:", r.stderr.strip()[:800])
    return r

# 1. Snapshot the compose project names running
ssh("cd /home/ubuntu/supabase/docker && docker compose ps --format '{{.Name}} {{.Status}}' | head -30", timeout=60)

# 2. Stop supabase stack (containers only, keep volumes/data for rollback)
ssh("cd /home/ubuntu/supabase/docker && docker compose stop 2>&1 | tail -30", timeout=300)
