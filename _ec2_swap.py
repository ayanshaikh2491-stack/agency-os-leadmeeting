import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=60):
    full = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=12",
            "-i", KEY, HOST, cmd]
    r = subprocess.run(full, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return r

# 1. Add 2GB swap
print("===== ADD SWAP =====")
cmd = (
    "sudo fallocate -l 2G /swapfile 2>/dev/null || sudo dd if=/dev/zero of=/swapfile bs=1M count=2048; "
    "sudo chmod 600 /swapfile; "
    "sudo mkswap /swapfile; "
    "sudo swapon /swapfile; "
    "grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab; "
    "swapon --show; free -m"
)
r = ssh(cmd, timeout=120)
print(r.stdout)
if r.stderr.strip():
    print("STDERR:", r.stderr[-1000:])
