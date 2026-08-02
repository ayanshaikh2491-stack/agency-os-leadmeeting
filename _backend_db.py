import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=60):
    full = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10",
            "-i", KEY, HOST, cmd]
    r = subprocess.run(full, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return r

# Find DB-related config in backend code
r = ssh("grep -n -i 'DATABASE_URL\\|postgres\\|supabase\\|SQLALCHEMY\\|DB_HOST\\|DB_URL\\|create_engine\\|psycopg' /opt/agency-platform/backend/main.py | head -30")
print("=== MAIN.PY DB REFS ===")
print(r.stdout[:2500])

r2 = ssh("grep -rn -i 'DATABASE_URL\\|postgres\\|supabase' /opt/agency-platform/backend/agent_engine.py | head -20")
print("\n=== AGENT_ENGINE DB REFS ===")
print(r2.stdout[:2000])

# Check systemd services
r3 = ssh("systemctl cat agency-backend 2>/dev/null | head -25; echo ====; systemctl list-units --type=service --state=failed 2>/dev/null | head -10")
print("\n=== SYSTEMD ===")
print(r3.stdout[:2500])
