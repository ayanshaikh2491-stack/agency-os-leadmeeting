"""Pull EC2 sba_reason.py and diff against git HEAD."""
import os, subprocess, sys
sys.path.insert(0, os.getcwd())

KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

r = subprocess.run(
    ["scp", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
     "-o", "ConnectTimeout=10", "-i", KEY,
     f"{HOST}:/home/ubuntu/sba-backend/admin/agency/sba_reason.py",
     os.path.join(os.getcwd(), "deploy", "_ec2_sba_reason.py")],
    capture_output=True, text=True, timeout=120, encoding="utf-8", errors="replace")
print("pull rc:", r.returncode, r.stderr[-300:])

# diff against git HEAD
r = subprocess.run(["git", "show", "HEAD:admin/agency/sba_reason.py"],
                   capture_output=True, text=True, timeout=60, encoding="utf-8", errors="replace")
open(os.path.join(os.getcwd(), "deploy", "_head_sba_reason.py"), "w", encoding="utf-8").write(r.stdout)

# quick unified diff via fc / python
import difflib
head = open("deploy/_head_sba_reason.py", encoding="utf-8").read().splitlines()
ec2 = open("deploy/_ec2_sba_reason.py", encoding="utf-8").read().splitlines()
diff = list(difflib.unified_diff(head, ec2, "HEAD", "EC2", lineterm=""))
print("\n".join(diff[:120]) if diff else "IDENTICAL to HEAD")
