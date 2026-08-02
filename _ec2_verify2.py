import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=45):
    full = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10",
            "-i", KEY, HOST, cmd]
    r = subprocess.run(full, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return r

# Get ANON key from env properly
r = ssh("grep '^ANON_KEY=' /home/ubuntu/supabase/docker/.env | head -1 | cut -d= -f2- | tr -d '\\r\\n' | wc -c")
print("ANON key length:", r.stdout[:100])

r2 = ssh("export ANON=$(grep '^ANON_KEY=' /home/ubuntu/supabase/docker/.env | head -1 | cut -d= -f2- | tr -d '\\r\\n'); curl -s -w '\\nHTTP:%{http_code}' http://localhost:8050/rest/v1/ -H 'apikey: '$ANON -H 'Authorization: Bearer '$ANON | tail -3")
print("REST with anon:", r2.stdout[:600])

r3 = ssh("curl -s -o /dev/null -w 'studio via kong: %{http_code}' http://localhost:8050/studio/")
print(r3.stdout[:300])

# public schema tables via REST
r4 = ssh("export ANON=$(grep '^ANON_KEY=' /home/ubuntu/supabase/docker/.env | head -1 | cut -d= -f2- | tr -d '\\r\\n'); curl -s http://localhost:8050/rest/v1/clients?select=name -H 'apikey: '$ANON -H 'Authorization: Bearer '$ANON")
print("clients query:", r4.stdout[:600])
