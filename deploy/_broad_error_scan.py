import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

script = r'''
echo "=== ERROR/Traceback count per service (today) ==="
for svc in sba sba-autopilot sba-gateway sba-chrome pocketbase; do
  n=$(sudo journalctl -u $svc.service --since '2026-08-09 00:00:00' --no-pager 2>/dev/null | grep -icE "traceback|error|exception" || echo 0)
  echo "$svc: $n"
done
echo
echo "=== sba.service last ERROR lines (if any) ==="
sudo journalctl -u sba.service --since '2026-08-09 00:00:00' --no-pager | grep -iE "traceback|error|exception" | tail -6 || echo "none"
echo
echo "=== sba-chrome last ERROR lines ==="
sudo journalctl -u sba-chrome.service --since '2026-08-09 00:00:00' --no-pager | grep -iE "traceback|error|exception" | tail -6 || echo "none"
echo
echo "=== /api/status full ==="
curl -s -m 15 http://127.0.0.1:8000/api/status | python3 -m json.tool 2>/dev/null | head -40
echo
echo "=== organic scheduler activity ==="
sudo journalctl -u sba.service --since '2026-08-09 00:00:00' --no-pager | grep -iE "organic|scheduler|dispatch" | tail -5 || echo "none"
'''

r = subprocess.run(
    ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-i", KEY, HOST, script],
    capture_output=True, text=True, timeout=180,
)
print(r.stdout)
if r.stderr:
    print("STDERR:", r.stderr[:1000])
print("rc=", r.returncode)
