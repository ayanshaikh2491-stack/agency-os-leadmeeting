import subprocess, os

os.chdir(r"C:\Users\TAUSHEF\Downloads\int")
KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
                    "-i", KEY, HOST, "cat /tmp/pb_import_run.log 2>/dev/null | tail -40"],
                   capture_output=True, text=True, timeout=60, encoding="utf-8", errors="replace")
print("rc=", r.returncode)
print(r.stdout.strip()[:4000])
if r.stderr.strip():
    print("ERR:", r.stderr.strip()[:500])
