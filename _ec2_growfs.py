import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=120):
    full = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10",
            "-i", KEY, HOST, cmd]
    r = subprocess.run(full, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return r

r = ssh("sudo growpart /dev/nvme0n1 1 2>&1; sudo resize2fs /dev/nvme0n1p1 2>&1 | tail -3; df -h / | tail -1")
print(r.stdout[:2000])
if r.stderr.strip():
    print("ERR:", r.stderr[-400:])
