import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

files = ["main.py", "agent_engine.py", "ceo_agent.py", "oauth_handler.py"]
for f in files:
    scp = ["scp", "-o", "StrictHostKeyChecking=no", "-i", KEY,
           HOST + f":/opt/agency-platform/backend/{f}",
           rf"C:\Users\TAUSHEF\Downloads\int\_backend_{f}"]
    r = subprocess.run(scp, capture_output=True, text=True, timeout=90, encoding="utf-8", errors="replace")
    print(f, "rc:", r.returncode, r.stderr[-200:])

# systemd units
scp2 = ["scp", "-o", "StrictHostKeyChecking=no", "-i", KEY,
        HOST + ":/etc/systemd/system/agency-backend.service",
        r"C:\Users\TAUSHEF\Downloads\int\_agency-backend.service"]
r = subprocess.run(scp2, capture_output=True, text=True, timeout=90, encoding="utf-8", errors="replace")
print("service rc:", r.returncode, r.stderr[-200:])
