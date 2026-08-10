import subprocess, os

os.chdir(r"C:\Users\TAUSHEF\Downloads\int")
KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=60):
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
                        "-o", "ConnectTimeout=10", "-i", KEY, HOST, cmd],
                       capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    print("rc=", r.returncode)
    print(r.stdout.strip()[:4000])
    if r.stderr.strip():
        print("ERR:", r.stderr.strip()[:500])
    return r

# Check how backend does counts / reads Content-Range
ssh("grep -rn 'Content-Range\\|content-range\\|limit=0\\|select=count' /home/ubuntu/sba-backend/admin --include='*.py' | head -20")
