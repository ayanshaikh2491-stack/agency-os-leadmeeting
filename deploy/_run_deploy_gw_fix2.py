import subprocess, os

os.chdir(r"C:\Users\TAUSHEF\Downloads\int")
KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=90):
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
                        "-o", "ConnectTimeout=10", "-i", KEY, HOST, cmd],
                       capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    print("rc=", r.returncode)
    print(r.stdout.strip()[:2000])
    if r.stderr.strip():
        print("ERR:", r.stderr.strip()[:500])
    return r

# 1. Kill old nohup gateway
ssh("pkill -f 'uvicorn pb_gateway'; sleep 1; ps aux | grep pb_gateway | grep -v grep | wc -l")

# 2. Install unit
ssh("sudo cp /tmp/sba-gateway.service /etc/systemd/system/sba-gateway.service && sudo systemctl daemon-reload && sudo systemctl enable sba-gateway.service && echo UNIT_OK")

# 3. Start and check
ssh("sudo systemctl restart sba-gateway.service; sleep 4; sudo systemctl is-active sba-gateway.service")
ssh("curl -sf http://127.0.0.1:8095/api/health && echo GATEWAY_OK || echo GATEWAY_NOT_UP")
