"""Deploy SBA backend to EC2 - step by step"""
import subprocess, os, time

KEY_SRC = 'C:/Users/TAUSHEF/Downloads/int/agency-backend-key-20260521.pem'
KEY_DST = 'C:/Users/TAUSHEF/Downloads/int/ec2-key.pem'
HOST = '18.213.66.136'
REMOTE_USER = 'ubuntu'
REMOTE_DIR = '/home/ubuntu/sba-backend'

# Ensure key exists at dst with right perms
if not os.path.exists(KEY_DST):
    import shutil
    shutil.copy2(KEY_SRC, KEY_DST)
    os.chmod(KEY_DST, 0o600)
    print(f'Key copied to {KEY_DST}')

ssh = ['ssh', '-i', KEY_DST, '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=10', 
       '-o', 'UserKnownHostsFile=/dev/null', f'{REMOTE_USER}@{HOST}']
scp = ['scp', '-i', KEY_DST, '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=10',
       '-o', 'UserKnownHostsFile=/dev/null']

def run(cmd, timeout=30):
    print(f'RUN: {cmd[:80]}...')
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if r.stdout.strip(): print(f'OUT: {r.stdout[:300]}')
    if r.stderr.strip(): print(f'ERR: {r.stderr[:200]}')
    return r.returncode

# 1. Create dirs
print('\n=== 1. Creating directories ===')
rc = run(ssh + ['mkdir', '-p', 
    f'{REMOTE_DIR}/admin/agency',
    f'{REMOTE_DIR}/admin/api/routes',
    f'{REMOTE_DIR}/admin/config',
    f'{REMOTE_DIR}/admin/tools',
    f'{REMOTE_DIR}/admin/api/models',
    f'{REMOTE_DIR}/admin/workspace',
])
if rc != 0:
    print(f'FAILED mkdir: {rc}')
    exit(1)

# 2. Copy files
print('\n=== 2. Copying files ===')
local_root = 'C:/Users/TAUSHEF/Downloads/int/admin'
scp_remote = f'{REMOTE_USER}@{HOST}:{REMOTE_DIR}/admin/'

for item in [
    'main.py',
    'requirements.txt',
    '__init__.py',
]:
    src = os.path.join(local_root, item)
    if os.path.exists(src):
        rc = run(scp + [src, scp_remote], timeout=15)
        print(f'  {"OK" if rc==0 else "FAIL"} {item}')

for item in [
    'agency/__init__.py', 'agency/sba.py', 'agency/sba_skills.py', 'agency/sba_store.py',
    'agency/ceo.py', 'agency/agency_agents.py', 'agency/swarm.py',
    'api/__init__.py',
    'api/models/__init__.py', 'api/models/schemas.py',
    'api/routes/__init__.py', 'api/routes/sba.py', 'api/routes/ceo.py',
    'api/routes/swarm.py', 'api/routes/workspace.py',
    'config/__init__.py', 'config/settings.py',
    'tools/__init__.py', 'tools/chrome_tool.py',
    'workspace/__init__.py', 'workspace/manager.py',
]:
    src = os.path.join(local_root, item)
    dst = os.path.join(scp_remote, os.path.dirname(item)) + '/'
    if os.path.exists(src):
        rc = run(scp + [src, dst], timeout=15)
        print(f'  {"OK" if rc==0 else "FAIL"} {item}')

# 3. Install deps
print('\n=== 3. Installing Python dependencies ===')
rc = run(ssh + [
    'cd', REMOTE_DIR, '&&',
    'pip3 install fastapi uvicorn httpx python-multipart pydantic anthropic 2>&1 | tail -5'
], timeout=120)
print(f'pip install: {"OK" if rc==0 else "FAIL (rc="+str(rc)+")"}')

# 4. Copy .env
print('\n=== 4. Copying .env ===')
env_path = 'C:/Users/TAUSHEF/Downloads/int/admin/.env'
if os.path.exists(env_path):
    rc = run(scp + [env_path, scp_remote], timeout=15)
    print(f'.env: {"OK" if rc==0 else "FAIL"}')

# 5. Test run
print('\n=== 5. Starting backend ===')
rc = run(ssh + [
    'cd', REMOTE_DIR, '&&',
    'nohup python3 admin/main.py > /tmp/sba.log 2>&1 &',
    'sleep 3 && curl -s http://localhost:9002/health'
], timeout=15)

print('\n=== DONE ===')
