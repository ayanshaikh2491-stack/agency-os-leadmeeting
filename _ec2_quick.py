import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=25):
    full = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=8",
            "-i", KEY, HOST, cmd]
    r = subprocess.run(full, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return r

tests = [
    ("home dir", "ls /home/ubuntu/ | head"),
    ("opt dir", "ls /opt/agency-platform/backend | head"),
    ("venv", "ls /opt/agency-platform/backend/venv/bin 2>/dev/null | head -5"),
    ("pip packages", "python3 -c \"import fastapi, uvicorn; print('fastapi ok')\" 2>&1"),
    ("load", "uptime"),
    ("free mem", "free -m | head -2"),
]
for name, cmd in tests:
    try:
        r = ssh(cmd)
        print(f"--- {name} ---")
        print((r.stdout or "")[:500])
        if r.stderr.strip():
            print("ERR:", r.stderr[-200:])
    except Exception as e:
        print(f"--- {name} TIMEOUT: {e}")
