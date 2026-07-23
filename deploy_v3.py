"""Deploy SBA to EC2 - using string commands like ec2_connect.py"""
import subprocess, os

KEY = 'C:/Users/TAUSHEF/Downloads/int/ec2-key.pem'
HOST = 'ubuntu@18.213.66.136'
BASE = ['ssh', '-i', KEY, '-o', 'StrictHostKeyChecking=no', '-o', 'UserKnownHostsFile=/dev/null', '-o', 'ConnectTimeout=5', HOST]
SCP = ['scp', '-i', KEY, '-o', 'StrictHostKeyChecking=no', '-o', 'UserKnownHostsFile=/dev/null', '-o', 'ConnectTimeout=5']

def run(cmd_list, timeout=30):
    r = subprocess.run(cmd_list, capture_output=True, text=True, timeout=timeout)
    if r.stdout.strip(): print(r.stdout[:500])
    if r.stderr.strip(): print('ERR:', r.stderr[:200])
    print(f'RC={r.returncode}')
    return r.returncode

# Step 0: Test connection
print('=== Step 0: Test SSH ===')
rc = run(BASE + ['hostname'], timeout=10)
if rc != 0:
    print('SSH FAILED. Trying to fix key...')
    # Copy key fresh
    import shutil
    src = 'C:/Users/TAUSHEF/.ssh/agency-backend-key-20260521.pem'
    if os.path.exists(src):
        shutil.copy2(src, KEY)
        os.chmod(KEY, 0o600)
        print('Key recopied')
        rc = run(BASE + ['hostname'], timeout=10)
        if rc != 0:
            print('Still fails. Exiting.')
            exit(1)

# Step 1: Create dirs
print('\n=== Step 1: Create dirs ===')
run(BASE + ['mkdir -p /home/ubuntu/sba-backend/admin/{agency,api/routes,api/models,config,tools,workspace}'], timeout=30)

# Step 2: Copy root files
print('\n=== Step 2: Copy files ===')
local = 'C:/Users/TAUSHEF/Downloads/int/admin'
remote = f'{HOST}:/home/ubuntu/sba-backend/admin/'

for f in ['main.py', 'requirements.txt', '__init__.py', '.env']:
    src = os.path.join(local, f)
    if os.path.exists(src):
        run(SCP + [src, remote], timeout=30)

# Deep copy agency/
print('--- agency/ ---')
run(SCP + [os.path.join(local, 'agency/__init__.py'), os.path.join(local, 'agency/sba.py'),
           os.path.join(local, 'agency/sba_skills.py'), os.path.join(local, 'agency/sba_store.py'),
           os.path.join(local, 'agency/ceo.py'), os.path.join(local, 'agency/agency_agents.py'),
           os.path.join(local, 'agency/swarm.py'),
           f'{HOST}:/home/ubuntu/sba-backend/admin/agency/'], timeout=30)

print('--- api/ ---')
for f in ['api/__init__.py', 'api/routes/__init__.py', 'api/routes/sba.py', 'api/routes/ceo.py',
          'api/routes/swarm.py', 'api/routes/workspace.py', 'api/models/__init__.py', 'api/models/schemas.py']:
    run(SCP + [os.path.join(local, f), f'{HOST}:/home/ubuntu/sba-backend/admin/{os.path.dirname(f)}/'], timeout=30)

print('--- config/ tools/ workspace/ ---')
for d in ['config/__init__.py', 'config/settings.py', 'tools/__init__.py', 'tools/chrome_tool.py',
          'workspace/__init__.py', 'workspace/manager.py']:
    run(SCP + [os.path.join(local, d), f'{HOST}:/home/ubuntu/sba-backend/admin/{os.path.dirname(d)}/'], timeout=30)

# Step 3: Install deps
print('\n=== Step 3: Install deps ===')
run(BASE + ['cd /home/ubuntu/sba-backend && pip3 install fastapi uvicorn httpx python-multipart pydantic 2>&1 | tail -5'], timeout=120)

# Step 4: Start backend
print('\n=== Step 4: Start backend ===')
run(BASE + ['cd /home/ubuntu/sba-backend && nohup python3 admin/main.py > /tmp/sba.log 2>&1 &'], timeout=15)

# Step 5: Check
print('\n=== Step 5: Check ===')
run(BASE + ['sleep 3 && curl -s http://localhost:9002/health'], timeout=15)

print('\n=== DONE ===')
