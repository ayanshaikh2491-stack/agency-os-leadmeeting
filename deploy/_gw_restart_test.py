import subprocess, os, signal, sys, time, urllib.request, json

os.chdir(r"C:\Users\TAUSHEF\Downloads\int\deploy")

def sh(cmd, timeout=60):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(">>>", cmd)
    print(r.stdout.strip()[:2000])
    if r.stderr.strip():
        print("ERR:", r.stderr.strip()[:400])
    return r

# kill old gateway (pid 16096)
sh("powershell -Command \"Stop-Process -Id 16096 -Force -ErrorAction SilentlyContinue\"")
time.sleep(2)

# start new gateway with patched code
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
time.sleep(3)
try:
    r = urllib.request.urlopen("http://127.0.0.1:8095/api/health", timeout=5)
    print("HEALTH", json.load(r))
except Exception as e:
    print("HEALTH_FAIL", e)
    err = proc.stderr.read().decode() if proc.stderr else ""
    print("STDERR", err[:600])
    proc.terminate()
    sys.exit(1)

# run gateway tests against local PB
r = sh("python _pb_gw_test.py", timeout=180)
