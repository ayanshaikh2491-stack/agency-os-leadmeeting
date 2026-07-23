import subprocess
key = 'ec2-key.pem'
host = 'ubuntu@18.213.66.136'
r = subprocess.run(['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no', host,
    'docker --version 2>/dev/null; echo ===; docker compose version 2>/dev/null; echo ===; which docker 2>/dev/null || echo no_docker'],
    capture_output=True, text=True, timeout=10)
print(r.stdout)
if r.stderr.strip(): print('ERR:', r.stderr[:300])
