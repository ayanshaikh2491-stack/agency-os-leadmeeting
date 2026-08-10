import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

def run(remote_cmd, timeout=90):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-i", KEY, HOST, remote_cmd],
        capture_output=True, text=True, timeout=timeout,
    )
    print(r.stdout)
    if r.stderr:
        print("STDERR:", r.stderr[:500])
    print("rc=", r.returncode)
    return r

# 1. Latest autopilot pass summary
run("sudo journalctl -u sba-autopilot.service --since '30 min ago' --no-pager | grep -E 'pass|emails_sent|no_email|deferred|error' | tail -15")

# 2. Autopilot service health
run("systemctl is-active sba-autopilot.service sba.service sba-gateway.service pocketbase.service && systemctl show sba-autopilot.service -p NRestarts -p ActiveEnterTimestamp")

# 3. Gateway health + lead count
run("curl -s http://127.0.0.1:8095/api/health && echo && curl -s 'http://127.0.0.1:8095/rest/v1/leads?select=id&limit=1' | head -c 200")
