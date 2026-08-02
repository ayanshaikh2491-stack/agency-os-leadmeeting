import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=45):
    full = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10",
            "-i", KEY, HOST, cmd]
    r = subprocess.run(full, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return r

r = ssh("tail -8 /tmp/supabase_up.log; echo ----; docker ps --format '{{.Names}} {{.Status}}' | head -15")
print(r.stdout[:3000])
if r.stderr.strip():
    print("ERR:", r.stderr[-400:])
