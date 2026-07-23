"""Step by step: Deploy to EC2"""
import subprocess, time, os, tarfile, tempfile

KEY = 'C:/Users/TAUSHEF/Downloads/int/ec2-key.pem'
HOST = 'ubuntu@18.213.66.136'
REMOTE = '/home/ubuntu/sba-backend'

def ssh(cmd, timeout=60):
    full = ['ssh', '-i', KEY, '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null', '-o', 'ConnectTimeout=30', HOST, cmd]
    r = subprocess.run(full, capture_output=True, timeout=timeout)
    o = r.stdout.decode('utf-8', errors='replace')
    e = r.stderr.decode('utf-8', errors='replace')
    if o.strip(): print(o[:400])
    if e.strip() and 'Warning' not in e:
        for line in e.split('\n')[:3]:
            if line.strip(): print('E:', line[:200])
    return r.returncode

# Step 1: Kill old process
print('=== 1. Kill old ===')
ssh('pkill -f admin.main 2>/dev/null; echo killed', timeout=30)

# Step 2: Check files on EC2
print('\n=== 2. Check files ===')
ssh(f'ls {REMOTE}/admin/main.py 2>/dev/null && echo EXISTS || echo MISSING', timeout=30)

# Step 3: Send updated files via tar pipe
print('\n=== 3. Send updated files ===')
tar_path = os.path.join(tempfile.gettempdir(), 'sba_deploy3.tar.gz')
with tarfile.open(tar_path, 'w:gz') as tar:
    tar.add('admin', arcname='admin')
print(f'Tar size: {os.path.getsize(tar_path)/1024:.1f} KB')

ssh_cmd = ['ssh', '-i', KEY, '-o', 'StrictHostKeyChecking=no',
           '-o', 'UserKnownHostsFile=/dev/null', '-o', 'ConnectTimeout=30',
           HOST, f'cd {REMOTE} && tar xzf -']
with open(tar_path, 'rb') as f:
    r = subprocess.run(ssh_cmd, stdin=f, capture_output=True, timeout=60)
    if r.returncode == 0:
        print('✅ Files sent')
    else:
        print('❌ Send failed:', r.stderr[:200].decode('utf-8', errors='replace'))

# Step 4: Check venv
print('\n=== 4. Check venv ===')
rc = ssh(f'ls {REMOTE}/venv/bin/python 2>/dev/null && echo VENV_OK || echo NO_VENV', timeout=30)

# Step 5: Start backend
print('\n=== 5. Start backend ===')
rc = ssh(f'cd {REMOTE} && PYTHONPATH={REMOTE} nohup venv/bin/python -m admin.main > /tmp/sba.log 2>&1 & echo started', timeout=30)
# Always succeeds for background

# Step 6: Wait + health
print('\n=== 6. Health check ===')
time.sleep(6)
rc = ssh(f'curl -s --max-time 5 http://localhost:9002/api/health', timeout=30)

# Step 7: Log
print('\n=== 7. Log ===')
rc = ssh(f'tail -20 /tmp/sba.log', timeout=30)

print('\n🎉 Done EC2 deploy!')
