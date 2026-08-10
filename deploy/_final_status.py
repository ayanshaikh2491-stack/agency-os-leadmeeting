import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

script = r'''
echo "=== services ==="
systemctl is-active sba.service sba-autopilot.service sba-gateway.service sba-chrome.service pocketbase.service
systemctl show sba-autopilot.service -p NRestarts
echo "=== gateway health ==="
curl -s http://127.0.0.1:8095/api/health
echo
echo "=== disk/mem ==="
df -h / | tail -1
free -h | grep Mem
echo "=== last 2 pass summaries ==="
sudo journalctl -u sba-autopilot.service --no-pager | grep -E 'autopilot pass:' | tail -2
echo "=== any errors since fix? ==="
sudo journalctl -u sba-autopilot.service --since '2026-08-09 16:44:30' --no-pager | grep -cE "ERROR|Traceback|lead finding pass failed"
'''

r = subprocess.run(
    ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-i", KEY, HOST, script],
    capture_output=True, text=True, timeout=120,
)
print(r.stdout)
if r.stderr:
    print("STDERR:", r.stderr[:1000])
print("rc=", r.returncode)
