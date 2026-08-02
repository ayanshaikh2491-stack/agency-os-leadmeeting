import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"
SCHEMA = r"C:\Users\TAUSHEF\Downloads\int\agency-frontend\supabase\schema.sql"

def ssh(cmd, timeout=120):
    full = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10",
            "-i", KEY, HOST, cmd]
    r = subprocess.run(full, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return r

# Upload schema
scp = ["scp", "-o", "StrictHostKeyChecking=no", "-i", KEY, SCHEMA, HOST + ":/home/ubuntu/schema.sql"]
r = subprocess.run(scp, capture_output=True, text=True, timeout=90, encoding="utf-8", errors="replace")
print("SCP rc:", r.returncode, r.stderr[-300:])

# Apply schema in supabase-db container
r2 = ssh("docker cp /home/ubuntu/schema.sql supabase-db:/tmp/schema.sql && docker exec supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=0 -f /tmp/schema.sql 2>&1 | tail -25")
print("\n=== APPLY SCHEMA ===")
print(r2.stdout[:4000])
if r2.stderr.strip():
    print("ERR:", r2.stderr[-500:])
