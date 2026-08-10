import subprocess, os

os.chdir(r"C:\Users\TAUSHEF\Downloads\int")
KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=40):
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
                        "-o", "ConnectTimeout=8", "-i", KEY, HOST, cmd],
                       capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    print("rc=", r.returncode)
    print(r.stdout.strip()[:3500])
    if r.stderr.strip():
        print("ERR:", r.stderr.strip()[:400])
    return r

print("=== where autopilot loads leads (imports) ===")
ssh("grep -n 'import\\|from ' /home/ubuntu/sba-backend/admin/agency/sba_autopilot.py | head -40")
print("=== who queries leads table ===")
ssh("grep -rln 'rest/v1/leads' /home/ubuntu/sba-backend/admin --include='*.py'")
print("=== lead query with page/limit in sba store or db layer ===")
ssh("grep -rn 'rest/v1/leads' /home/ubuntu/sba-backend/admin --include='*.py' | grep -iE 'page|limit|order|select' | head -20")
