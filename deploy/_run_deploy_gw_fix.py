import subprocess, os, sys

os.chdir(r"C:\Users\TAUSHEF\Downloads\int")
KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def run(args, timeout=120):
    r = subprocess.run(args, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    print(r.stdout)
    if r.stderr:
        print("STDERR:", r.stderr[:800])
    print("rc=", r.returncode)
    return r

# 1. upload fixed gateway
run(["scp", "-o", "StrictHostKeyChecking=no", "-i", KEY,
     "deploy/pb_gateway.py", HOST + ":/home/ubuntu/sba-backend/pb_gateway.py"], 60)

# 2. install systemd unit for gateway (survives reboot)
unit = """[Unit]
Description=SBA PocketBase Supabase Gateway
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/ubuntu/sba-backend
Environment=PB_URL=http://127.0.0.1:8090
Environment=PB_ADMIN_EMAIL=admin@tagsagency.local
Environment=PB_ADMIN_PASS=pb-admin-2026-x9
Environment=PB_ENV_FILE=/home/ubuntu/sba-backend/.env
ExecStart=/home/ubuntu/sba-backend/venv/bin/python -m uvicorn pb_gateway:app --host 127.0.0.1 --port 8095
Restart=always
RestartSec=5
User=ubuntu

[Install]
WantedBy=multi-user.target
"""
unit_path = os.path.join(os.getcwd(), "deploy", "sba-gateway.service")
with open(unit_path, "w") as f:
    f.write(unit)

run(["scp", "-o", "StrictHostKeyChecking=no", "-i", KEY,
     unit_path, HOST + ":/tmp/sba-gateway.service"], 60)

run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-i", KEY, HOST,
     "pkill -f 'uvicorn pb_gateway' 2>/dev/null; sleep 1; "
     "sudo cp /tmp/sba-gateway.service /etc/systemd/system/sba-gateway.service && "
     "sudo systemctl daemon-reload && "
     "sudo systemctl enable sba-gateway.service && "
     "sudo systemctl restart sba-gateway.service && "
     "sleep 4 && "
     "curl -sf http://127.0.0.1:8095/api/health && echo ' GATEWAY_OK' || echo 'GATEWAY_NOT_UP'"], 90)
