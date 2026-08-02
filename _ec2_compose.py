import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=40):
    full = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=12",
            "-i", KEY, HOST, cmd]
    r = subprocess.run(full, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return r

print("===== COMPOSE SERVICES & PORTS =====")
r = ssh("cd /home/ubuntu/supabase/docker && grep -E '^  [a-z-]+:|published:|target:' docker-compose.yml | head -120")
print(r.stdout[:5000])
if r.stderr.strip():
    print("STDERR:", r.stderr[-800:])

print("\n===== NATIVE PG USER =====")
r = ssh("sudo -u postgres psql -c '\\l' 2>&1 | head -20")
print(r.stdout[:2000])
