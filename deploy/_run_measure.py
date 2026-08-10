import subprocess, os, sys

os.chdir(r"C:\Users\TAUSHEF\Downloads\int")
KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

print("scp script...")
r = subprocess.run(
    ["scp", "-o", "StrictHostKeyChecking=no", "-i", KEY,
     "deploy/_measure_supabase.sh", HOST + ":/home/ubuntu/_measure_supabase.sh"],
    capture_output=True, text=True, timeout=60)
print("scp rc=", r.returncode, (r.stderr or "")[:300])

print("run script...")
r = subprocess.run(
    ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-i", KEY,
     HOST, "bash /home/ubuntu/_measure_supabase.sh"],
    capture_output=True, text=True, timeout=120)
print(r.stdout)
if r.stderr:
    print("STDERR:", r.stderr[:500])
print("rc=", r.returncode)
