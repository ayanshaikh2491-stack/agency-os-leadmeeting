import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=45):
    full = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10",
            "-i", KEY, HOST, cmd]
    r = subprocess.run(full, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return r

r = ssh("""docker exec supabase-db psql -U postgres -d postgres -t -c "select name, phone, raw->>'phone' from leads where name = 'P V Auto Services' limit 1;" """)
print("Q1:", r.stdout[:600], r.stderr[-300:])

r2 = ssh("""docker exec supabase-db psql -U postgres -d postgres -t -c "select count(*) filter (where phone is null or phone='') as no_phone, count(*) as total from leads;" """)
print("Q2:", r2.stdout[:400])
