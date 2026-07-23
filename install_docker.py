import subprocess
key = 'ec2-key.pem'
host = 'ubuntu@18.213.66.136'

# Use Docker's convenience script - fastest way
cmds = [
    'curl -fsSL https://get.docker.com -o /tmp/get-docker.sh',
    'sudo sh /tmp/get-docker.sh 2>&1 | tail -5',
    'sudo usermod -aG docker ubuntu',
]
for cmd in cmds:
    r = subprocess.run(['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no', host, cmd],
        capture_output=True, text=True, timeout=120)
    print(f"$ {cmd[:50]}...")
    if r.stdout.strip(): print(r.stdout[:200])
    if r.stderr.strip(): print("ERR:", r.stderr[:200])

# Verify docker
r = subprocess.run(['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no', host,
    'sudo docker --version; sudo docker compose version'],
    capture_output=True, text=True, timeout=10)
print("Version:", r.stdout)
