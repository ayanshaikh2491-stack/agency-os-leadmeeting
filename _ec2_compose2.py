import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=40):
    full = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=12",
            "-i", KEY, HOST, cmd]
    r = subprocess.run(full, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return r

# Show ports per service with context
r = ssh("cd /home/ubuntu/supabase/docker && grep -n -A3 'ports:' docker-compose.yml | head -100")
print("=== PORTS ===")
print(r.stdout[:4500])
if r.stderr.strip():
    print("STDERR:", r.stderr[-600:])

print("\n=== FIRST 80 LINES ===")
r2 = ssh("cd /home/ubuntu/supabase/docker && head -80 docker-compose.yml")
print(r2.stdout[:4500])
