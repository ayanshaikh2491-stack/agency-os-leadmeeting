import subprocess

# Kill the stale leftover aws login (PID 14680, created 11:19:02, task cancelled)
# Keep PID 12740 (the one whose URL/code state we used)
r = subprocess.run(["taskkill", "/PID", "14680", "/F"], capture_output=True, text=True)
print("kill 14680:", r.stdout, r.stderr)
