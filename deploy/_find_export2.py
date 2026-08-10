import subprocess, os

os.chdir(r"C:\Users\TAUSHEF\Downloads\int")
KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=40):
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
                        "-o", "ConnectTimeout=10", "-i", KEY, HOST, cmd],
                       capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    print("rc=", r.returncode)
    print(r.stdout.strip()[:3000])
    if r.stderr.strip():
        print("ERR:", r.stderr.strip()[:500])
    return r

# find export script - limited scope
ssh("ls -la /home/ubuntu/*.sh /home/ubuntu/*.py 2>/dev/null | grep -iE 'export|dump|backup' | head -10")
ssh("ls -la /home/ubuntu/sba-backend/*.sh /home/ubuntu/sba-backend/*.py 2>/dev/null | grep -iE 'export|dump|backup' | head -10")
