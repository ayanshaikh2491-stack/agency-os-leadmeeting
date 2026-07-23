"""Deploy SBA to EC2 - using Python-native tar pipe (works on Windows)"""
import subprocess, os, shutil, tarfile, tempfile, sys

KEY = 'C:/Users/TAUSHEF/Downloads/int/ec2-key.pem'
HOST = 'ubuntu@18.213.66.136'

# Ensure key
if not os.path.exists(KEY):
    src = 'C:/Users/TAUSHEF/.ssh/agency-backend-key-20260521.pem'
    if os.path.exists(src):
        shutil.copy2(src, KEY)
        os.chmod(KEY, 0o600)

local = 'C:/Users/TAUSHEF/Downloads/int/admin'
remote_dir = '/home/ubuntu/sba-backend'

# Step 1: Create tar in memory
print('=== Step 1: Creating tar ===')
tar_path = os.path.join(tempfile.gettempdir(), 'sba_deploy.tar.gz')
with tarfile.open(tar_path, 'w:gz') as tar:
    tar.add(local, arcname='admin')
print(f'Tar size: {os.path.getsize(tar_path)/1024:.0f} KB')

# Step 2: Pipe tar over SSH
print('=== Step 2: Sending to EC2 ===')
ssh = ['ssh', '-i', KEY, '-o', 'StrictHostKeyChecking=no',
       '-o', 'ConnectTimeout=10', '-o', 'UserKnownHostsFile=/dev/null',
       HOST, f'cd {remote_dir} && tar xzf -']

with open(tar_path, 'rb') as f:
    r = subprocess.run(ssh, stdin=f, capture_output=True, text=False, timeout=60)
    if r.returncode == 0:
        print('✅ Files transferred!')
    else:
        print(f'❌ Transfer failed: {r.stderr[:200]}')
        sys.exit(1)

# Step 3: Create workspace dir
print('=== Step 3: Workspace dir ===')
ssh2 = ['ssh', '-i', KEY, '-o', 'StrictHostKeyChecking=no',
        '-o', 'ConnectTimeout=10', '-o', 'UserKnownHostsFile=/dev/null',
        HOST, 'mkdir -p /home/ubuntu/sba-backend/admin/workspace']
subprocess.run(ssh2, capture_output=True, text=True, timeout=30)

# Step 4: Install deps
print('=== Step 4: pip install ===')
ssh3 = ['ssh', '-i', KEY, '-o', 'StrictHostKeyChecking=no',
        '-o', 'ConnectTimeout=10', '-o', 'UserKnownHostsFile=/dev/null',
        HOST, 'pip3 install fastapi uvicorn httpx python-multipart pydantic 2>&1 | tail -5']
r = subprocess.run(ssh3, capture_output=True, text=True, timeout=180)
print(r.stdout or r.stderr[:200])

# Step 5: Start backend
print('=== Step 5: Start backend ===')
ssh4 = ['ssh', '-i', KEY, '-o', 'StrictHostKeyChecking=no',
        '-o', 'ConnectTimeout=10', '-o', 'UserKnownHostsFile=/dev/null',
        HOST, 'cd /home/ubuntu/sba-backend && nohup python3 admin/main.py > /tmp/sba.log 2>&1 &']
subprocess.run(ssh4, capture_output=True, text=True, timeout=30)

# Step 6: Wait + health check
print('=== Step 6: Health check ===')
import time
time.sleep(5)
ssh5 = ['ssh', '-i', KEY, '-o', 'StrictHostKeyChecking=no',
        '-o', 'ConnectTimeout=10', '-o', 'UserKnownHostsFile=/dev/null',
        HOST, 'curl -s --max-time 5 http://localhost:9002/health']
r = subprocess.run(ssh5, capture_output=True, text=True, timeout=30)
print(f'Health: {r.stdout[:300]}')

# Step 7: Log
print('=== Step 7: Log ===')
ssh6 = ['ssh', '-i', KEY, '-o', 'StrictHostKeyChecking=no',
        '-o', 'ConnectTimeout=10', '-o', 'UserKnownHostsFile=/dev/null',
        HOST, 'tail -30 /tmp/sba.log']
r = subprocess.run(ssh6, capture_output=True, text=True, timeout=30)
print(r.stdout[:500])
if r.stderr.strip() and 'Warning' not in r.stderr:
    print('ERR:', r.stderr[:200])

print('\n🎉 DONE!')
