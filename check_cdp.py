import subprocess, sys
key = 'ec2-key.pem'
host = 'ubuntu@18.213.66.136'

r = subprocess.run(['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no', host,
    'sudo systemctl status sba-chrome --no-pager 2>&1; echo ===STATUS===; sudo systemctl is-active sba-chrome 2>&1; echo ===CDP===; curl -s http://localhost:9222/json/version 2>&1; echo ===HEALTH===; curl -s http://localhost:8000/api/health 2>&1; echo ===SBA===; curl -s http://localhost:8000/api/sba/status 2>&1'],
    capture_output=True, timeout=20)

out = r.stdout.decode('utf-8', errors='replace')
print(out[-1500:])
