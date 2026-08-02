import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=45):
    full = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10",
            "-i", KEY, HOST, cmd]
    r = subprocess.run(full, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return r

# Test kong endpoint from inside EC2
r = ssh("curl -s -o /dev/null -w '%{http_code}' http://localhost:8050/rest/v1/ -H 'apikey: $(grep ANON_KEY /home/ubuntu/supabase/docker/.env | head -1 | cut -d= -f2- | tr -d \\r)'")
print("Kong /rest/v1/ status:", r.stdout[:200])

r2 = ssh("curl -s -o /dev/null -w '%{http_code}' http://localhost:8050")
print("Kong root status:", r2.stdout[:200])

r3 = ssh("curl -s -o /dev/null -w '%{http_code}' http://localhost:3000")  # studio
print("Studio status:", r3.stdout[:200])

# Postgres version
r4 = ssh("docker exec supabase-db psql -U postgres -c 'select version();' | head -3")
print("\nPG:", r4.stdout[:300])
