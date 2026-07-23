"""Deploy SBA to EC2 - with proper timeouts"""
import subprocess, os, shutil

KEY = 'C:/Users/TAUSHEF/Downloads/int/ec2-key.pem'
HOST = 'ubuntu@18.213.66.136'

# Ensure key exists
if not os.path.exists(KEY):
    src = 'C:/Users/TAUSHEF/.ssh/agency-backend-key-20260521.pem'
    if os.path.exists(src):
        shutil.copy2(src, KEY)
        os.chmod(KEY, 0o600)
        print('Key copied')

def ssh_run(cmd_str, timeout=30):
    full = ['ssh', '-i', KEY, '-o', 'StrictHostKeyChecking=no',
            '-o', 'ConnectTimeout=10', '-o', 'UserKnownHostsFile=/dev/null',
            HOST, cmd_str]
    r = subprocess.run(full, capture_output=True, text=True, timeout=timeout)
    if r.stdout.strip(): print(r.stdout.strip())
    if r.stderr.strip() and 'Warning' not in r.stderr: print('ERR:', r.stderr.strip()[:300])
    return r.returncode

def scp(src, dst, timeout=30):
    full = ['scp', '-i', KEY, '-o', 'StrictHostKeyChecking=no',
            '-o', 'ConnectTimeout=10', '-o', 'UserKnownHostsFile=/dev/null',
            src, f'{HOST}:{dst}']
    r = subprocess.run(full, capture_output=True, text=True, timeout=timeout)
    if r.stderr.strip() and 'Warning' not in r.stderr:
        print('ERR:', r.stderr.strip()[:200])
    return r.returncode

# Step 0: Test
print('=== Step 0: Test SSH ===')
rc = ssh_run('hostname && uptime', timeout=25)
if rc != 0:
    print('SSH FAILED!')
    exit(1)

# Step 1: Dirs
print('\n=== Step 1: Dirs ===')
ssh_run('mkdir -p /home/ubuntu/sba-backend/admin/agency /home/ubuntu/sba-backend/admin/api/routes /home/ubuntu/sba-backend/admin/api/models /home/ubuntu/sba-backend/admin/config /home/ubuntu/sba-backend/admin/tools /home/ubuntu/sba-backend/admin/workspace')

# Step 2: Copy files
print('\n=== Step 2: Copy files ===')
local = 'C:/Users/TAUSHEF/Downloads/int/admin'
rd = '/home/ubuntu/sba-backend/admin/'

file_map = {
    '': ['main.py', 'requirements.txt', '__init__.py', '.env'],
    'agency/': ['__init__.py', 'sba.py', 'sba_skills.py', 'sba_store.py', 'ceo.py', 'agency_agents.py', 'swarm.py'],
    'api/': ['__init__.py'],
    'api/routes/': ['__init__.py', 'sba.py', 'ceo.py', 'swarm.py', 'workspace.py'],
    'api/models/': ['__init__.py', 'schemas.py'],
    'config/': ['__init__.py', 'settings.py'],
    'tools/': ['__init__.py', 'chrome_tool.py'],
    'workspace/': ['__init__.py', 'manager.py'],
}

for subdir, files in file_map.items():
    for f in files:
        src = os.path.join(local, subdir.replace('/', '\\'), f)
        if os.path.exists(src):
            r = scp(src, rd + subdir)
            status = 'OK' if r == 0 else 'FAIL'
        else:
            status = 'MISS'
        print(f'  [{status}] {subdir}{f}')

# Step 3: Install pip deps
print('\n=== Step 3: Install deps ===')
ssh_run('pip3 install fastapi uvicorn httpx python-multipart pydantic 2>&1 | tail -5', timeout=180)

# Step 4: Start
print('\n=== Step 4: Start backend ===')
ssh_run('cd /home/ubuntu/sba-backend && nohup python3 admin/main.py > /tmp/sba.log 2>&1 &')

# Step 5: Check
print('\n=== Step 5: Health check ===')
ssh_run('sleep 5 && curl -s --max-time 5 http://localhost:9002/health', timeout=30)

# Step 6: Log
print('\n=== Step 6: Log ===')
ssh_run('tail -30 /tmp/sba.log')

print('\n🎉 DONE!')
