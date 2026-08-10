import subprocess, os

os.chdir(r"C:\Users\TAUSHEF\Downloads\int")
KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

for step in [
    ["scp", "-o", "StrictHostKeyChecking=no", "-i", KEY,
     "deploy/_remote_count2.sh", HOST + ":/tmp/_remote_count2.sh"],
    ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
     "-i", KEY, HOST, "bash /tmp/_remote_count2.sh"],
]:
    print("=" * 30)
    r = subprocess.run(step, capture_output=True, text=True, timeout=180, encoding="utf-8", errors="replace")
    print("rc=", r.returncode)
    print(r.stdout.strip()[:5000])
    if r.stderr.strip():
        print("ERR:", r.stderr.strip()[:800])
