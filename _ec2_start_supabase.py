import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=60):
    full = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=12",
            "-i", KEY, HOST, cmd]
    r = subprocess.run(full, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return r

# Start supabase stack detached, log to file
r = ssh("cd /home/ubuntu/supabase/docker && nohup docker compose up -d > /tmp/supabase_up.log 2>&1 & echo STARTED_PID=$!")
print("START:", r.stdout[:200], r.stderr[:300])
