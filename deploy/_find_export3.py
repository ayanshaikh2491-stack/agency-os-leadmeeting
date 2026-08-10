import subprocess, os

os.chdir(r"C:\Users\TAUSHEF\Downloads\int")
KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

cmds = [
    "ls -la /home/ubuntu/*.sh 2>/dev/null | head -20",
    "ls -la /home/ubuntu/sba-backend/*.py 2>/dev/null | grep -iE 'export|dump|backup|sync' | head -10",
    "ls -la /home/ubuntu/pb_export/ | head -3",
]
for cmd in cmds:
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
                        "-o", "ConnectTimeout=10", "-i", KEY, HOST, cmd],
                       capture_output=True, text=True, timeout=40, encoding="utf-8", errors="replace")
    print("CMD:", cmd[:80], "rc=", r.returncode)
    print(r.stdout.strip()[:2500])
    if r.stderr.strip():
        print("ERR:", r.stderr.strip()[:400])
    print()
