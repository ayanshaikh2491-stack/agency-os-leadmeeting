import subprocess
key = 'ec2-key.pem'
host = 'ubuntu@18.213.66.136'

r = subprocess.run(['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no', host,
    'sudo journalctl -u sba --no-pager --since "5 min ago" 2>&1; echo ===; tail -50 /tmp/sba.log 2>&1'],
    capture_output=True, timeout=30)
out = r.stdout.decode('utf-8', errors='replace')
print(out[-2000:])
