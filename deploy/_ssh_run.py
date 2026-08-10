import subprocess, sys

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"
cmd = sys.argv[1] if len(sys.argv) > 1 else "echo CONN_OK; hostname; uptime"
r = subprocess.run(
    ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
     "-o", "ConnectTimeout=10", "-i", KEY, HOST, cmd],
    capture_output=True, text=True, timeout=45, encoding="utf-8", errors="replace",
)
print("RC:", r.returncode)
print("STDOUT:", r.stdout)
print("STDERR:", r.stderr)
