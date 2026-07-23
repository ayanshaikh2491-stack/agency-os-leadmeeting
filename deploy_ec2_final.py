"""Deploy updated SBA backend to EC2 + connect frontend"""
import subprocess, time, os, tarfile, tempfile

KEY = 'C:/Users/TAUSHEF/Downloads/int/ec2-key.pem'
HOST = 'ubuntu@18.213.66.136'
REMOTE = '/home/ubuntu/sba-backend'

# --- Step 1: Tar and send updated backend ---
print('=== 1. Sending updated backend to EC2 ===')
tar_path = os.path.join(tempfile.gettempdir(), 'sba_deploy2.tar.gz')
with tarfile.open(tar_path, 'w:gz') as tar:
    tar.add('admin', arcname='admin')

ssh = ['ssh', '-i', KEY, '-o', 'StrictHostKeyChecking=no',
       '-o', 'UserKnownHostsFile=/dev/null', '-o', 'ConnectTimeout=15', HOST]

# Kill old + extract new
with open(tar_path, 'rb') as f:
    r = subprocess.run(ssh + [f'cd {REMOTE} && pkill -f admin.main 2>/dev/null; tar xzf -'],
                       stdin=f, capture_output=True, timeout=60)
    print('Extract:', 'OK' if r.returncode == 0 else 'FAIL')
    if r.stderr[:200]: print('ERR:', r.stderr[:200].decode('utf-8', errors='replace'))

# --- Step 2: Start backend on EC2 ---
print('\n=== 2. Starting backend on EC2 ===')
r = subprocess.run(ssh + [f'cd {REMOTE} && PYTHONPATH={REMOTE} nohup venv/bin/python -m admin.main > /tmp/sba.log 2>&1 & echo STARTED'],
                   capture_output=True, text=True, timeout=15)
print(r.stdout[:200])
if r.stderr[:200]: print('ERR:', r.stderr[:200])

time.sleep(5)

# --- Step 3: Check health ---
print('\n=== 3. Health check ===')
r = subprocess.run(ssh + ['curl -s --max-time 5 http://localhost:9002/api/health'],
                   capture_output=True, text=True, timeout=15)
print('EC2 Health:', r.stdout[:200])

# --- Step 4: Update frontend proxy to EC2 ---
print('\n=== 4. Updating frontend proxy to EC2 ===')
frontend_route = 'C:/Users/TAUSHEF/Downloads/int/agency-frontend/src/app/api/sba/route.js'
if os.path.exists(frontend_route):
    with open(frontend_route, encoding='utf-8', errors='replace') as f:
        content = f.read()
    old = 'http://localhost:9002'
    new = 'http://18.213.66.136:9002'
    if old in content:
        content = content.replace(old, new)
        with open(frontend_route, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'✅ Frontend proxy updated: {old} -> {new}')
    else:
        print(f'Current proxy target: check manually')
        for line in content.split('\n')[:5]:
            print(f'  {line}')
else:
    print(f'Frontend route file not found at {frontend_route}')

# Step 5: Also check .env.local for frontend
env_local = 'C:/Users/TAUSHEF/Downloads/int/agency-frontend/.env.local'
if os.path.exists(env_local):
    with open(env_local, encoding='utf-8', errors='replace') as f:
        print('\n=== 5. Frontend .env.local ===')
        print(f.read()[:500])

print('\n🎉 Done!')
