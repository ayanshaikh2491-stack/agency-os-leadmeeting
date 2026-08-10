import subprocess, sys, os

# Start gateway locally on 8095 pointing at local PB 8090
env = dict(os.environ)
env["PB_URL"] = "http://127.0.0.1:8090"
env["PB_ENV_FILE"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_test.env")

proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "pb_gateway:app", "--host", "127.0.0.1", "--port", "8095", "--log-level", "warning"],
    cwd=os.path.dirname(os.path.abspath(__file__)),
    env=env,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.PIPE,
)
print("GW_PID", proc.pid)
import time
time.sleep(3)

# health check
import urllib.request, json
try:
    r = urllib.request.urlopen("http://127.0.0.1:8095/api/health", timeout=5)
    print("HEALTH", json.load(r))
except Exception as e:
    print("HEALTH_FAIL", e)
    err = proc.stderr.read().decode() if proc.stderr else ""
    print("STDERR", err[:500])
    proc.terminate()
    sys.exit(1)
