import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

script = r'''
sudo journalctl -u sba-autopilot.service --since '2026-08-09 16:44:30' --no-pager | grep -E 'autopilot pass:' | tail -5
echo "=== enrichment working? ==="
sudo journalctl -u sba-autopilot.service --since '2026-08-09 16:44:30' --no-pager | grep -E 'enriched|ERROR|Traceback' | tail -6
'''

r = subprocess.run(
    ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-i", KEY, HOST, script],
    capture_output=True, text=True, timeout=120,
)
print(r.stdout)
if r.stderr:
    print("STDERR:", r.stderr[:1000])
print("rc=", r.returncode)
