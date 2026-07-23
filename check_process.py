import subprocess
key = 'ec2-key.pem'
host = 'ubuntu@18.213.66.136'

r = subprocess.run(['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no', host,
    'ps aux | grep admin.main | grep -v grep; echo RC=$?; echo ===; ls /tmp/sba.log 2>&1; echo ===; tail -20 /tmp/sba.log 2>&1'],
    capture_output=True, timeout=15)
out = r.stdout.decode('utf-8', errors='replace')
print(out[-1500:])
if r.stderr:
    print(r.stderr.decode('utf-8', errors='replace')[:300])
