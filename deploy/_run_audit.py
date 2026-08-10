import subprocess, os

os.chdir(r"C:\Users\TAUSHEF\Downloads\int")
KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

# upload audit script then run it
p = subprocess.run(["scp", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
                    "-i", KEY, "deploy/_audit_data.sh", f"{HOST}:/tmp/_audit_data.sh"],
                   capture_output=True, text=True, timeout=60, encoding="utf-8", errors="replace")
print("scp rc=", p.returncode, p.stderr.strip()[:300])

r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
                    "-o", "ConnectTimeout=10", "-i", KEY, HOST, "bash /tmp/_audit_data.sh"],
                   capture_output=True, text=True, timeout=120, encoding="utf-8", errors="replace")
print("rc=", r.returncode)
print(r.stdout.strip()[:5000])
if r.stderr.strip():
    print("ERR:", r.stderr.strip()[:600])
