import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=60):
    full = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=12",
            "-i", KEY, HOST, cmd]
    r = subprocess.run(full, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return r

r = ssh("cat /home/ubuntu/supabase/docker/.env.example")
open(r"C:\Users\TAUSHEF\Downloads\int\_supabase_env_example.txt", "w", encoding="utf-8").write(r.stdout)
print("ENV SAVED, lines:", r.stdout.count("\n"))

r2 = ssh("sudo ss -tlnp | grep -v docker | head -40")
print("\n=== LISTENING PORTS (non-docker) ===")
print(r2.stdout[:3000])
if r2.stderr.strip():
    print("STDERR:", r2.stderr[-400:])
