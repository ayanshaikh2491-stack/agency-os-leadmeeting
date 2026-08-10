import subprocess, os

os.chdir(r"C:\Users\TAUSHEF\Downloads\int")
KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=60):
    print(">>>", cmd)
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
                        "-o", "ConnectTimeout=8", "-i", KEY, HOST, cmd],
                       capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    print("rc=", r.returncode)
    print(r.stdout.strip()[:2500])
    if r.stderr.strip():
        print("ERR:", r.stderr.strip()[:400])
    return r

# copy patched gateway to the path the service actually imports
ssh("cp /home/ubuntu/sba-backend/deploy/pb_gateway.py /home/ubuntu/sba-backend/pb_gateway.py && python3 -m py_compile /home/ubuntu/sba-backend/pb_gateway.py && echo COPIED_OK")
ssh("grep -c '_build_limit' /home/ubuntu/sba-backend/pb_gateway.py")
ssh("sudo systemctl restart sba-gateway.service && sleep 3 && systemctl is-active sba-gateway.service")
ssh("curl -s -m 10 http://127.0.0.1:8095/health; echo")
