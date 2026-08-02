import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=60):
    full = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=12",
            "-i", KEY, HOST, cmd]
    r = subprocess.run(full, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return r

r = ssh("cat /home/ubuntu/supabase/docker/docker-compose.yml")
out = r.stdout
open(r"C:\Users\TAUSHEF\Downloads\int\_supabase_compose.yml", "w", encoding="utf-8").write(out)
print("SAVED, lines:", out.count("\n"))
print("STDERR:", (r.stderr or "")[-400:])
