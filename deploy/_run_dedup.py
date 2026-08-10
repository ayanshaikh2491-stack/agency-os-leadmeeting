import subprocess, os

os.chdir(r"C:\Users\TAUSHEF\Downloads\int")
KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def run(args, timeout=240):
    r = subprocess.run(args, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    print("rc=", r.returncode)
    print(r.stdout.strip()[:3000])
    if r.stderr.strip():
        print("ERR:", r.stderr.strip()[:600])
    return r

# 1. upload fixed gateway (page fix) + dedup script
run(["scp", "-o", "StrictHostKeyChecking=no", "-i", KEY,
     "deploy/pb_gateway.py", HOST + ":/home/ubuntu/sba-backend/pb_gateway.py"], 60)
run(["scp", "-o", "StrictHostKeyChecking=no", "-i", KEY,
     "deploy/_dedup_pb.py", HOST + ":/tmp/_dedup_pb.py"], 60)

# 2. restart gateway systemd
run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
     "-i", KEY, HOST, "sudo systemctl restart sba-gateway.service; sleep 4; sudo systemctl is-active sba-gateway.service"])

# 3. run dedup
run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
     "-i", KEY, HOST, "python3 /tmp/_dedup_pb.py"], 300)
