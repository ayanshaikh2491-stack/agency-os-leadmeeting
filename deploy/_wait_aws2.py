import subprocess
import time

for i in range(12):
    r = subprocess.run(["aws", "sts", "get-caller-identity", "--profile", "aws2"],
                       capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip()
    if r.returncode == 0:
        print("SUCCESS:")
        print(out)
        break
    else:
        print(f"try {i}: rc={r.returncode} {out[:200]}")
    time.sleep(5)
