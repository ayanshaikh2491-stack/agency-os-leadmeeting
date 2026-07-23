"""Deploy SBA to EC2"""
import subprocess, os

KEY = 'C:/Users/TAUSHEF/Downloads/int/ec2-key.pem'
HOST = 'ubuntu@18.213.66.136'

# Ensure key exists
if not os.path.exists(KEY):
    import shutil
    src = 'C:/Users/TAUSHEF/.ssh/agency-backend-key-20260521.pem'
    if os.path.exists(src):
        shutil.copy2(src, KEY)
        os.chmod(KEY, 0o600)
        print('Key copied')

def run(cmd_str, timeout=30):
    """Run a shell command string over SSH"""
    full = ['ssh', '-i', KEY, '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null', '-o', 'ConnectTimeout=5',
            HOST, cmd_str]
    r = subprocess.run(full, capture_output=True, text=True, timeout=timeout)
    if r.stdout.strip(): print(r.stdout)
    if r.stderr.strip(): print('ERR:', r.stderr[:300])
    print(f'RC={r.returncode}')
    return r.returncode

def scp(src, dst, timeout=30):
    """Copy a file to remote"""
    full = ['scp', '-i', KEY, '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null', '-o', 'ConnectTimeout=5',
            src, f'{HOST}:{dst}']
    r = subprocess.run(full, capture_output=True, text=True, timeout=timeout)
    if r.stderr.strip(): print('ERR:', r.stderr[:200])
    return r.returncode

# Step 0: Test connection
print('=== Step 0: Test SSH ===')
rc = run('hostname && uptime', timeout=20)
if rc != 0:
    print('SSH FAILED. Check key.')
    exit(1)

# Step 1: Create dirs
print('\n=== Step 1: Create dirs ===')
run('mkdir -p /home/ubuntu/sba-backend/admin/agency /home/ubuntu/sba-backend/admin/api/routes /home/ubuntu/sba-backend/admin/api/models /home/ubuntu/sba-backend/admin/config /home/ubuntu/sba-backend/admin/tools /home/ubuntu/sba-backend/admin/workspace', timeout=15)

# Step 2: Copy files
print('\n=== Step 2: Copy files ===')
local = 'C:/Users/TAUSHEF/Downloads/int/admin'
rd = '/home/ubuntu/sba-backend/admin/'

# Root files
for f in ['main.py', 'requirements.txt', '__init__.py', '.env']:
    src = os.path.join(local, f)
    if os.path.exists(src):
        rc = scp(src, rd, timeout=15)
        print(f'  {"OK" if rc==0 else "FAIL"} {f}')

# agency/
for f in ['__init__.py', 'sba.py', 'sba_skills.py', 'sba_store.py', 'ceo.py', 'agency_agents.py', 'swarm.py']:
    src = os.path.join(local, 'agency', f)
    if os.path.exists(src):
        rc = scp(src, rd + 'agency/', timeout=15)
        print(f'  {"OK" if rc==0 else "FAIL"} agency/{f}')

# api/
for f in ['__init__.py']:
    src = os.path.join(local, 'api', f)
    rc = scp(src, rd + 'api/', timeout=15) if os.path.exists(src) else 1
    print(f'  {"OK" if rc==0 else "MISS"} api/{f}')

for f in ['__init__.py', 'sba.py', 'ceo.py', 'swarm.py', 'workspace.py']:
    src = os.path.join(local, 'api/routes', f)
    rc = scp(src, rd + 'api/routes/', timeout=15) if os.path.exists(src) else 1
    print(f'  {"OK" if rc==0 else "MISS"} api/routes/{f}')

for f in ['__init__.py', 'schemas.py']:
    src = os.path.join(local, 'api/models', f)
    rc = scp(src, rd + 'api/models/', timeout=15) if os.path.exists(src) else 1
    print(f'  {"OK" if rc==0 else "MISS"} api/models/{f}')

# config/
for f in ['__init__.py', 'settings.py']:
    src = os.path.join(local, 'config', f)
    rc = scp(src, rd + 'config/', timeout=15) if os.path.exists(src) else 1
    print(f'  {"OK" if rc==0 else "MISS"} config/{f}')

# tools/
for f in ['__init__.py', 'chrome_tool.py']:
    src = os.path.join(local, 'tools', f)
    rc = scp(src, rd + 'tools/', timeout=15) if os.path.exists(src) else 1
    print(f'  {"OK" if rc==0 else "MISS"} tools/{f}')

# workspace/
for f in ['__init__.py', 'manager.py']:
    src = os.path.join(local, 'workspace', f)
    rc = scp(src, rd + 'workspace/', timeout=15) if os.path.exists(src) else 1
    print(f'  {"OK" if rc==0 else "MISS"} workspace/{f}')

# Step 3: Install deps
print('\n=== Step 3: Install deps ===')
run('cd /home/ubuntu/sba-backend && pip3 install fastapi uvicorn httpx python-multipart pydantic 2>&1 | tail -5', timeout=120)

# Step 4: Start backend
print('\n=== Step 4: Start backend ===')
run('cd /home/ubuntu/sba-backend && nohup python3 admin/main.py > /tmp/sba.log 2>&1 &', timeout=10)

# Step 5: Check
print('\n=== Step 5: Check health ===')
run('sleep 4 && curl -s --max-time 5 http://localhost:9002/health', timeout=15)

# Step 6: Show log if failed
print('\n=== Step 6: Log tail (if any) ===')
run('tail -20 /tmp/sba.log', timeout=10)

print('\n=== DONE ===')
