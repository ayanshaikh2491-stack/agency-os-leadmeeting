"""Deploy EC2 - optimized 2-step"""
import subprocess, os, tarfile, tempfile, time

KEY = 'ec2-key.pem'
HOST = 'ubuntu@18.213.66.136'
REMOTE = '/home/ubuntu/sba-backend'

# Step 1: Tar pipe - kill + extract + start in ONE connection
print('=== 1. Tar pipe: kill + extract + start ===')
tar_path = os.path.join(tempfile.gettempdir(), 'sba_deploy4.tar.gz')
with tarfile.open(tar_path, 'w:gz') as tar:
    tar.add('admin', arcname='admin')
print(f'Tar: {os.path.getsize(tar_path)/1024:.0f} KB')

# Single remote command chain
cmd = f'cd {REMOTE}; pkill -f admin.main 2>/dev/null; tar xzf -; PYTHONPATH={REMOTE} nohup {REMOTE}/venv/bin/python -m admin.main > /tmp/sba.log 2>&1; echo STARTED'

ssh_cmd = ['ssh', '-i', KEY, '-o', 'StrictHostKeyChecking=no',
           '-o', 'UserKnownHostsFile=/dev/null', '-o', 'ConnectTimeout=20',
           HOST, cmd]

with open(tar_path, 'rb') as f:
    r = subprocess.run(ssh_cmd, stdin=f, capture_output=True, text=True, timeout=90)
    for line in r.stdout.split('\n')[:5]:
        if line.strip(): print(' ', line.strip())
    if r.stderr.strip() and 'Warning' not in r.stderr:
        for l in r.stderr.split('\n')[:3]:
            if l.strip(): print('E:', l[:150])

# Step 2: Wait + health
print('\n=== 2. Health ===')
time.sleep(6)
r2 = subprocess.run(['ssh', '-i', KEY, '-o', 'StrictHostKeyChecking=no',
                     '-o', 'UserKnownHostsFile=/dev/null', '-o', 'ConnectTimeout=20',
                     HOST, 'curl -s --max-time 5 http://localhost:9002/api/health'],
                    capture_output=True, text=True, timeout=30)
print('Health:', r2.stdout[:200])

# Log
r3 = subprocess.run(['ssh', '-i', KEY, '-o', 'StrictHostKeyChecking=no',
                     '-o', 'UserKnownHostsFile=/dev/null', '-o', 'ConnectTimeout=20',
                     HOST, 'tail -15 /tmp/sba.log'],
                    capture_output=True, text=True, timeout=30)
print('Log:', r3.stdout[:400] if r3.stdout.strip() else '(empty)')

print('\n🎉 Done!')
