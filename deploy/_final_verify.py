import subprocess, os

os.chdir(r"C:\Users\TAUSHEF\Downloads\int")
KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=120):
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
                        "-o", "ConnectTimeout=10", "-i", KEY, HOST, cmd],
                       capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    print("rc=", r.returncode)
    print(r.stdout.strip()[:4000])
    if r.stderr.strip():
        print("ERR:", r.stderr.strip()[:500])
    return r

print("=== service status ===")
ssh("systemctl is-active sba.service sba-autopilot.service sba-gateway.service sba-chrome.service; echo '---'; systemctl is-active sba-pb.service 2>/dev/null || echo 'sba-pb: n/a'", timeout=30)
print("=== ports: 8090 (PB), 8095 (gateway), 8050 (supabase-kong, should be closed) ===")
ssh("ss -tlnp | grep -E ':(8090|8095|8050|8000)\\b' || echo 'none of the ports listening'", timeout=30)
print("=== health checks ===")
ssh("echo -n 'pb: '; curl -s http://127.0.0.1:8090/api/health; echo; echo -n 'gateway: '; curl -s http://127.0.0.1:8095/health; echo; echo -n 'backend: '; curl -s http://127.0.0.1:8000/api/health; echo", timeout=60)
print("=== memory + docker ===")
ssh("free -h | head -3; echo '---'; docker ps -a --format '{{.Names}} {{.Status}}' | head -25", timeout=60)
print("=== gateway errors today ===")
ssh("sudo journalctl -u sba-gateway.service --no-pager --since '08:00' | grep -c ' 500 ' || true", timeout=60)
print("=== autopilot after supabase stop ===")
ssh("sudo journalctl -u sba-autopilot.service --since '3 minutes ago' --no-pager | tail -15", timeout=60)
