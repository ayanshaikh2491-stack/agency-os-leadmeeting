"""Deploy EC2 - everything in ONE SSH connection using tar pipe"""
import subprocess, os, tarfile, tempfile

KEY = 'ec2-key.pem'
HOST = 'ubuntu@18.213.66.136'
REMOTE = '/home/ubuntu/sba-backend'

# Step 1: Create tar
print('=== Creating tar ===')
tar_path = os.path.join(tempfile.gettempdir(), 'sba_quick.tar.gz')
with tarfile.open(tar_path, 'w:gz') as tar:
    tar.add('admin', arcname='admin')
print(f'Tar: {os.path.getsize(tar_path)/1024:.0f} KB')

# Step 2: Send via SSH pipe + everything in one go
print('=== Sending + Restarting ===')
# Build the remote commands
remote_cmds = f'''
cd {REMOTE}
echo "1. Kill old"
pkill -f admin.main 2>/dev/null
echo "2. Extract tar"
tar xzf -
echo "3. Start backend"
PYTHONPATH={REMOTE} nohup {REMOTE}/venv/bin/python -m admin.main > /tmp/sba.log 2>&1 &
echo "4. Started"
'''

ssh = ['ssh', '-i', KEY, '-o', 'StrictHostKeyChecking=no',
       '-o', 'UserKnownHostsFile=/dev/null', '-o', 'ConnectTimeout=20',
       HOST]

with open(tar_path, 'rb') as f:
    r = subprocess.run(ssh + [remote_cmds], stdin=f, capture_output=True, text=True, timeout=120)

print('STDOUT:', r.stdout[:500])
if r.stderr.strip() and 'Warning' not in r.stderr:
    print('STDERR:', r.stderr[:300])

# Step 3: Verify after a few seconds
print('\n=== Verifying ===')
import time
time.sleep(6)
r2 = subprocess.run(ssh + ['curl -s --max-time 5 http://localhost:9002/api/health'],
                    capture_output=True, text=True, timeout=30)
print('Health:', r2.stdout[:200])
if r2.stderr.strip() and 'Warning' not in r2.stderr:
    print('STDERR:', r2.stderr[:200])

# Step 4: Check log
print('\n=== Log ===')
r3 = subprocess.run(ssh + ['tail -15 /tmp/sba.log'],
                    capture_output=True, text=True, timeout=30)
print(r3.stdout[:500])
if r3.stderr.strip() and 'Warning' not in r3.stderr:
    print('STDERR:', r3.stderr[:200])

print('\n🎉 DONE!')
