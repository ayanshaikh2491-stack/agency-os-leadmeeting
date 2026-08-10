import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

script = r'''
sudo journalctl -u sba-autopilot.service --since '2026-08-09 16:44:30' --no-pager | grep -E 'autopilot pass|lead finding|lead rotation|WARNING|ERROR|Traceback|found .* new leads' | tail -15
echo "---"
systemctl is-active sba-autopilot.service
systemctl show sba-autopilot.service -p NRestarts
'''

r = subprocess.run(
    ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-i", KEY, HOST, script],
    capture_output=True, text=True, timeout=120,
)
print(r.stdout)
if r.stderr:
    print("STDERR:", r.stderr[:1000])
print("rc=", r.returncode)
