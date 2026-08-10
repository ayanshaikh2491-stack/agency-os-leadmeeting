import subprocess, os, time

os.chdir(r"C:\Users\TAUSHEF\Downloads\int")
KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

for i in range(6):
    time.sleep(5)
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
                        "-i", KEY, HOST, "cat /tmp/pb_import_run2.log 2>/dev/null | tail -30"],
                       capture_output=True, text=True, timeout=30, encoding="utf-8", errors="replace")
    out = r.stdout.strip()
    if "DONE" in out:
        print(out[-3000:])
        break
    else:
        print(f"--- poll {i} ---")
        print(out[-1200:])
