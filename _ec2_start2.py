import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=45):
    full = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10",
            "-i", KEY, HOST, cmd]
    r = subprocess.run(full, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return r

r = ssh("cd /home/ubuntu/supabase/docker && rm -f /tmp/supabase_up.log && nohup docker compose up -d > /tmp/supabase_up.log 2>&1 < /dev/null & disown; echo STARTED")
print("OUT:", r.stdout[:300])
print("ERR:", r.stderr[:300])
