import subprocess
key = 'ec2-key.pem'
host = 'ubuntu@18.213.66.136'

# Get detailed logs
r = subprocess.run(['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no', host,
    'sudo docker compose -f /home/ubuntu/rallly/docker-compose.yml logs --tail=50 rallly 2>&1'],
    capture_output=True, text=True, timeout=30)
print(r.stdout)
if r.stderr.strip(): print(r.stderr[:300])
