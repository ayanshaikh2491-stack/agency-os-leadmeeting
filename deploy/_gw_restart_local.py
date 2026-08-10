import subprocess, os, signal, time, sys

# Kill any existing local gateway uvicorn on 8095, then restart with new code
KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"

def kill_8095_local():
    out = subprocess.run(["powershell", "-Command",
        "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*pb_gateway*8095*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    print("kill:", out.stdout.strip(), out.stderr.strip()[:200])

kill_8095_local()
time.sleep(1)

env = dict(os.environ)
env["PB_URL"] = "http://127.0.0.1:8090"
env["PB_ENV_FILE"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_test.env")

proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "pb_gateway:app", "--host", "127.0.0.1", "--port", "8095", "--log-level", "warning"],
    cwd=os.path.dirname(os.path.abspath(__file__)),
    env=env,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
print("GW_PID", proc.pid)
# Note: script exits; child keeps running detached
