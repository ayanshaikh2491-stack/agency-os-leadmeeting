import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=45):
    full = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10",
            "-i", KEY, HOST, cmd]
    r = subprocess.run(full, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return r

r = ssh("tail -15 /tmp/supabase_up.log")
print("=== UP LOG ===")
print(r.stdout[:2500])
if r.stderr.strip():
    print("ERR:", r.stderr[-300:])

r2 = ssh("docker ps --format '{{.Names}} | {{.Status}}' | sort")
print("\n=== CONTAINERS ===")
print(r2.stdout[:3000])
