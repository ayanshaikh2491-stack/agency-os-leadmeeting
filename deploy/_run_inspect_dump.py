import subprocess, os, sys

os.chdir(r"C:\Users\TAUSHEF\Downloads\int")
KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def run(args, timeout=180):
    r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    print(r.stdout)
    if r.stderr:
        print("STDERR:", r.stderr[:800])
    print("rc=", r.returncode)
    return r

print("=== SCP INSPECT ===")
run(["scp", "-o", "StrictHostKeyChecking=no", "-i", KEY,
     "deploy/_ec2_inspect.sh", HOST + ":/home/ubuntu/_ec2_inspect.sh"], 60)
print("=== RUN INSPECT ===")
run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-i", KEY,
     HOST, "bash /home/ubuntu/_ec2_inspect.sh"], 90)

print("=== SCP DUMP ===")
run(["scp", "-o", "StrictHostKeyChecking=no", "-i", KEY,
     "deploy/_dump_supabase.sh", HOST + ":/home/ubuntu/_dump_supabase.sh"], 60)
print("=== RUN DUMP ===")
run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-i", KEY,
     HOST, "bash /home/ubuntu/_dump_supabase.sh"], 300)
