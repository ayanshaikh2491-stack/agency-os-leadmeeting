import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=180):
    full = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=12",
            "-i", KEY, HOST, cmd]
    r = subprocess.run(full, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return r

print("===== CLONE SUPABASE (sparse docker) =====")
cmd = (
    "cd /home/ubuntu && "
    "rm -rf supabase && "
    "git clone --depth 1 --filter=blob:none --sparse https://github.com/supabase/supabase.git && "
    "cd supabase && git sparse-checkout set docker && "
    "ls docker/ | head -40 && "
    "df -h / | tail -1"
)
r = ssh(cmd, timeout=240)
print(r.stdout[-2500:])
if r.stderr.strip():
    print("STDERR:", r.stderr[-1500:])
