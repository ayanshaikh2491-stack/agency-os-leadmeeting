"""Deploy SBA to EC2 - using tar pipe (single connection)"""
import subprocess, os, shutil, tarfile, tempfile

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

# Step 1: Create a tar of all files
print('=== Step 1: Creating tar archive ===')
tar_path = os.path.join(tempfile.gettempdir(), 'sba_deploy.tar.gz')
with tarfile.open(tar_path, 'w:gz') as tar:
    tar.add(local, arcname='admin')

# Step 2: Pipe tar over SSH to remote
print('=== Step 2: Sending to EC2 ===')
print(f'Tar size: {os.path.getsize(tar_path)/1024:.0f} KB')

# Build the SSH command
ssh_cmd = ['ssh', '-i', KEY, '-o', 'StrictHostKeyChecking=no',
           '-o', 'ConnectTimeout=10', '-o', 'UserKnownHostsFile=/dev/null',
           '-o', 'ServerAliveInterval=15', '-o', 'ServerAliveCountMax=3',
           HOST]

# First: extract tar on remote
cat_cmd = ['cat', tar_path]
untar_cmd = f'cd {remote_dir} && tar xzf -'

p1 = subprocess.Popen(cat_cmd, stdout=subprocess.PIPE)
p2 = subprocess.Popen(ssh_cmd + [untar_cmd], stdin=p1.stdout, 
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       text=False)
p1.stdout.close()
stdout, stderr = p2.communicate(timeout=120)
if p2.returncode == 0:
    print('Files transferred OK!')
else:
    print(f'Transfer failed: {stderr[:200]}')
    exit(1)

# Step 3: Create remaining dirs
print('=== Step 3: Creating extra dirs ===')
subprocess.run(ssh_cmd + ['mkdir -p /home/ubuntu/sba-backend/admin/workspace'], 
               capture_output=True, text=True, timeout=30)

# Step 4: Install deps
print('=== Step 4: Installing deps ===')
subprocess.run(ssh_cmd + ['cd /home/ubuntu/sba-backend && pip3 install fastapi uvicorn httpx python-multipart pydantic 2>&1 | tail -5'],
               capture_output=True, text=True, timeout=180)
print('Deps done!')

# Step 5: Start backend
print('=== Step 5: Starting backend ===')
subprocess.run(ssh_cmd + ['cd /home/ubuntu/sba-backend && nohup python3 admin/main.py > /tmp/sba.log 2>&1 &'],
               capture_output=True, text=True, timeout=30)

# Step 6: Check
print('=== Step 6: Health check ===')
r = subprocess.run(ssh_cmd + ['sleep 5 && curl -s --max-time 5 http://localhost:9002/health'],
                   capture_output=True, text=True, timeout=30)
print(r.stdout[:500])

# Step 7: Log
print('=== Step 7: Log ===')
r = subprocess.run(ssh_cmd + ['tail -30 /tmp/sba.log'],
                   capture_output=True, text=True, timeout=30)
print(r.stdout[:500])
if r.stderr.strip() and 'Warning' not in r.stderr:
    print('ERR:', r.stderr[:300])

print('\n🎉 DONE!')
