"""Check git modified files + EC2 versions to find all stale deps."""
import os, subprocess, sys, hashlib
sys.path.insert(0, os.getcwd())

KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=45):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
         "-o", "ConnectTimeout=10", "-i", KEY, HOST, cmd],
        capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return r

# git modified files
r = subprocess.run(["git", "status", "--short"], capture_output=True, text=True, timeout=60, encoding="utf-8")
modified = [l.split()[1] for l in r.stdout.splitlines() if l.startswith(" M")]
print("modified tracked:", modified)

# hash compare local vs EC2
for f in modified:
    if not os.path.exists(f):
        continue
    local = open(f, "rb").read()
    lh = hashlib.sha256(local).hexdigest()[:12]
    r2 = ssh(f"cd /home/ubuntu/sba-backend && sha256sum {f} 2>/dev/null | cut -c1-12")
    ec2h = r2.stdout.strip().split()[0] if r2.stdout.strip() else "MISSING"
    match = "SAME" if ec2h == lh else "DIFF"
    print(f"{f}: local={lh} ec2={ec2h} {match}")
