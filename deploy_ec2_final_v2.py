"""Full EC2 deploy - one script to rule them all"""
import subprocess, os, tarfile, tempfile, time

KEY = 'ec2-key.pem'
HOST = 'ubuntu@18.213.66.136'
REMOTE = '/home/ubuntu/sba-backend'

def ssh(cmd, timeout=45):
    """SSH with text mode - works reliably"""
    full = ['ssh', '-i', KEY, '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null', '-o', 'ConnectTimeout=15', HOST, cmd]
    r = subprocess.run(full, capture_output=True, text=True, timeout=timeout)
    if r.stdout.strip():
        for line in r.stdout.strip().split('\n')[:5]:
            print(' ', line)
    if r.stderr.strip() and 'Warning' not in r.stderr:
        for line in r.stderr.strip().split('\n')[:3]:
            print('E:', line[:200])
    return r.returncode

# 1. Test connection
print('=== 1. Testing SSH ===')
ssh('hostname && uptime', timeout=25)

# 2. Kill old + create dirs
print('\n=== 2. Prep ===')
ssh('pkill -f admin.main 2>/dev/null; mkdir -p /home/ubuntu/sba-backend/admin/workspace/agents', timeout=25)

# 3. Tar and send files
print('\n=== 3. Sending files ===')
tar_path = os.path.join(tempfile.gettempdir(), 'sba_deploy_final.tar.gz')
with tarfile.open(tar_path, 'w:gz') as tar:
    tar.add('admin', arcname='admin')
print(f'  Tar: {os.path.getsize(tar_path)/1024:.0f} KB')

ssh_send = ['ssh', '-i', KEY, '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null', '-o', 'ConnectTimeout=15',
            HOST, f'cd {REMOTE} && tar xzf -']
with open(tar_path, 'rb') as f:
    r = subprocess.run(ssh_send, stdin=f, capture_output=True, text=True, timeout=60)
    print('  OK' if r.returncode == 0 else '  FAIL')

# 4. Create venv if needed
print('\n=== 4. Venv ===')
rc = ssh(f'ls {REMOTE}/venv/bin/python 2>/dev/null || (cd {REMOTE} && python3 -m venv venv && echo CREATED)', timeout=30)

# 5. Install deps
print('\n=== 5. pip install ===')
ssh(f'{REMOTE}/venv/bin/pip install fastapi uvicorn httpx python-multipart pydantic 2>&1 | tail -3', timeout=180)

# 6. Test import - simple
print('\n=== 6. Test import ===')
ssh(f'cd {REMOTE} && PYTHONPATH={REMOTE} {REMOTE}/venv/bin/python --version', timeout=25)

# 7. Start backend
print('\n=== 7. Start ===')
ssh(f'cd {REMOTE} && PYTHONPATH={REMOTE} nohup {REMOTE}/venv/bin/python -m admin.main > /tmp/sba.log 2>&1 & echo PID=$!', timeout=25)

# 8. Health
print('\n=== 8. Health ===')
time.sleep(6)
ssh(f'curl -s --max-time 5 http://localhost:9002/api/health', timeout=25)

# 9. Log
print('\n=== 9. Log ===')
ssh(f'tail -15 /tmp/sba.log', timeout=25)

print('\n🎉 EC2 Deploy Complete!')
print(f'🔗 http://18.213.66.136:9002/api/health')
