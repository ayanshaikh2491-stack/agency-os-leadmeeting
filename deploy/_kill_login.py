import subprocess

r = subprocess.run(["taskkill", "/PID", "12740", "/F"], capture_output=True, text=True)
print("kill 12740:", r.stdout, r.stderr)
