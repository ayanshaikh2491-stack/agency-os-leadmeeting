"""Deploy SBA to EC2 - Step 2: everything in one SSH connection"""
import subprocess, os, shutil, tarfile, tempfile, time

KEY = 'C:/Users/TAUSHEF/Downloads/int/ec2-key.pem'
HOST = 'ubuntu@18.213.66.136'

# Ensure key
if not os.path.exists(KEY):
    src = 'C:/Users/TAUSHEF/.ssh/agency-backend-key-20260521.pem'
    shutil.copy2(src, KEY)
    os.chmod(KEY, 0o600)

local = 'C:/Users/TAUSHEF/Downloads/int/admin'
remote_dir = '/home/ubuntu/sba-backend'

# Step 1: Create tar + pipe to EC2
print('=== Step 1: Tar + Send ===')
tar_path = os.path.join(tempfile.gettempdir(), 'sba_deploy.tar.gz')
with tarfile.open(tar_path, 'w:gz') as tar:
    tar.add(local, arcname='admin')
print(f'Tar: {os.path.getsize(tar_path)/1024:.0f} KB')

ssh_send = ['ssh', '-i', KEY, '-o', 'StrictHostKeyChecking=no',
            '-o', 'ConnectTimeout=15', '-o', 'UserKnownHostsFile=/dev/null',
            HOST, f'cd {remote_dir} && mkdir -p admin/workspace/agents && tar xzf -']

with open(tar_path, 'rb') as f:
    r = subprocess.run(ssh_send, stdin=f, capture_output=True, text=False, timeout=60)
    assert r.returncode == 0, f'Send failed: {r.stderr[:200]}'
print('✅ Files sent + dirs created')

# Step 2: Everything else in one SSH command
print('=== Step 2: Install deps + start ===')
ssh_cmd = ['ssh', '-i', KEY, '-o', 'StrictHostKeyChecking=no',
           '-o', 'ConnectTimeout=15', '-o', 'UserKnownHostsFile=/dev/null',
           HOST, '''
cd /home/ubuntu/sba-backend
echo "--- Installing deps ---"
pip3 install fastapi uvicorn httpx python-multipart pydantic 2>&1 | tail -3
echo "--- Starting backend ---"
nohup python3 admin/main.py > /tmp/sba.log 2>&1 &
echo "Waiting 6s..."
sleep 6
echo "--- Health check ---"
curl -s --max-time 5 http://localhost:9002/api/health
echo ""
echo "--- Log (last 15 lines) ---"
tail -15 /tmp/sba.log
echo "--- DONE ---"
''']

r = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=300)
print(r.stdout)
if r.stderr.strip() and 'Warning' not in r.stderr:
    print('STDERR:', r.stderr[:300])

# Step 3: Verify
print('\n=== Step 3: Verify from outside ===')
ssh3 = ['ssh', '-i', KEY, '-o', 'StrictHostKeyChecking=no',
        '-o', 'ConnectTimeout=15', '-o', 'UserKnownHostsFile=/dev/null',
        HOST, 'curl -s http://localhost:9002/api/health']
r3 = subprocess.run(ssh3, capture_output=True, text=True, timeout=30)
print(f'Health: {r3.stdout[:300]}')

print('\n🎉 DONE! Check http://18.213.66.136:9002/api/health')
