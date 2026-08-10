import subprocess, os

os.chdir(r"C:\Users\TAUSHEF\Downloads\int")
KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=90):
    print(">>>", cmd)
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
                        "-o", "ConnectTimeout=10", "-i", KEY, HOST, cmd],
                       capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    print("rc=", r.returncode)
    print(r.stdout.strip()[:3000])
    if r.stderr.strip():
        print("ERR:", r.stderr.strip()[:400])
    return r

# upload patched gateway
p = subprocess.run(["scp", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
                    "-i", KEY, "deploy/pb_gateway.py", f"{HOST}:/home/ubuntu/sba-backend/deploy/pb_gateway.py"],
                   capture_output=True, text=True, timeout=60, encoding="utf-8", errors="replace")
print("scp rc=", p.returncode, p.stderr.strip()[:300])

# syntax check + restart gateway
ssh("python3 -m py_compile /home/ubuntu/sba-backend/deploy/pb_gateway.py && echo SYNTAX_OK")
ssh("sudo systemctl restart sba-gateway.service && sleep 3 && systemctl is-active sba-gateway.service")
ssh("curl -s http://127.0.0.1:8095/health; echo")
