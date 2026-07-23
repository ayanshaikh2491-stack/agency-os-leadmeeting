import subprocess
key = 'ec2-key.pem'
host = 'ubuntu@18.213.66.136'
r = subprocess.run(['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no', host,
    'cat /tmp/sba.log 2>/dev/null; echo ===; ps aux | grep admin.main | grep -v grep; echo ===; curl -s http://localhost:8000/api/health || echo no_server'],
    capture_output=True, text=True, timeout=15)
print(r.stdout[-2000:])
if r.stderr.strip(): print('ERR:', r.stderr[:300])
