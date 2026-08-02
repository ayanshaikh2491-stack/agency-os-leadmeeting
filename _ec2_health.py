import subprocess, time

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=60):
    full = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=8",
            "-i", KEY, HOST, cmd]
    r = subprocess.run(full, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return r

tests = [
    ("memory", "free -m"),
    ("port8000", "sudo ss -tlnp | grep 8000"),
    ("docker mem", "docker stats --no-stream --format '{{.Name}} {{.MemUsage}}' | sort -k2 -h -r | head -15"),
    ("systemd failed", "systemctl --failed --no-legend | head"),
    ("what is on 8000", "ps aux | grep -i 'main.py\\|gunicorn\\|uvicorn' | grep -v grep | head"),
]
for name, cmd in tests:
    try:
        r = ssh(cmd, timeout=50)
        print(f"=== {name} ===")
        print((r.stdout or "")[:2000])
        if r.stderr.strip():
            print("ERR:", r.stderr[-200:])
    except Exception as e:
        print(f"=== {name} TIMEOUT: {str(e)[:100]}")
