import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=45):
    full = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10",
            "-i", KEY, HOST, cmd]
    r = subprocess.run(full, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return r

r = ssh("export SR=$(grep '^SERVICE_ROLE_KEY=' /home/ubuntu/supabase/docker/.env | head -1 | cut -d= -f2- | tr -d '\\r\\n'); curl -s 'http://localhost:8050/rest/v1/leads?select=name,status,phone&status=eq.good' -H 'apikey: '$SR -H 'Authorization: Bearer '$SR")
print("SERVICE ROLE good leads:", r.stdout[:1200])

r2 = ssh("export SR=$(grep '^SERVICE_ROLE_KEY=' /home/ubuntu/supabase/docker/.env | head -1 | cut -d= -f2- | tr -d '\\r\\n'); curl -s 'http://localhost:8050/rest/v1/leads?select=count' -H 'apikey: '$SR -H 'Authorization: Bearer '$SR")
print("\nSERVICE ROLE count:", r2.stdout[:300])
