import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"
ROOT = r"C:\Users\TAUSHEF\Downloads\int"

def sh(args, timeout=120):
    r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    print(r.stdout)
    if r.stderr:
        print("STDERR:", r.stderr[:800])
    print("rc=", r.returncode)
    return r

ssh = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-i", KEY, HOST]
scp = ["scp", "-o", "StrictHostKeyChecking=no", "-i", KEY]

# 1. Copy gateway to ROOT location (deploy gotcha: service imports root file)
sh(scp + [ROOT + r"\deploy\pb_gateway.py", HOST + ":/home/ubuntu/sba-backend/pb_gateway.py"])

# 2. Copy autopilot
sh(scp + [ROOT + r"\admin\agency\sba_autopilot.py", HOST + ":/home/ubuntu/sba-backend/admin/agency/sba_autopilot.py"])

# 3. Compile check on EC2
sh(ssh + ["cd /home/ubuntu/sba-backend && venv/bin/python -m py_compile pb_gateway.py admin/agency/sba_autopilot.py && echo COMPILE_OK"])

# 4. Restart gateway + autopilot
sh(ssh + ["sudo systemctl restart sba-gateway.service sba-autopilot.service && sleep 5 && systemctl is-active sba-gateway.service sba-autopilot.service"])
