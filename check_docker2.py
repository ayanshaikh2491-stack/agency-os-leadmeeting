import subprocess
key = 'ec2-key.pem'
host = 'ubuntu@18.213.66.136'
r = subprocess.run(['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no', host,
    'sudo docker --version 2>&1; echo ===; sudo which docker 2>&1; echo ===; sudo docker compose version 2>&1'],
    capture_output=True, text=True, timeout=10)
print(r.stdout)
if r.stderr.strip(): print(r.stderr[:300])
