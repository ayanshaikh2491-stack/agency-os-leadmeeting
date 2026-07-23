"""Fix SBA on EC2 - install deps properly + fix module path"""
import subprocess, os

KEY = 'C:/Users/TAUSHEF/Downloads/int/ec2-key.pem'
HOST = 'ubuntu@18.213.66.136'

def ssh(cmd_str, timeout=120):
    full = ['ssh', '-i', KEY, '-o', 'StrictHostKeyChecking=no',
            '-o', 'ConnectTimeout=15', '-o', 'UserKnownHostsFile=/dev/null',
            HOST, cmd_str]
    r = subprocess.run(full, capture_output=True, text=True, timeout=timeout)
    if r.stdout.strip(): print(r.stdout)
    if r.stderr.strip() and 'Warning' not in r.stderr:
        print('STDERR:', r.stderr[:300])
    return r.returncode

# 1. Fix pip - use venv
print('=== 1. Create venv + install deps ===')
ssh('''
cd /home/ubuntu/sba-backend
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn httpx python-multipart pydantic 2>&1 | tail -5
which python
python --version
''', timeout=180)

# 2. Test with venv
print('\n=== 2. Test import ===')
ssh('''
cd /home/ubuntu/sba-backend
source venv/bin/activate
python -c "import sys; sys.path.insert(0, '.'); from admin.api.models.schemas import HealthResponse; print('IMPORT OK')"
''', timeout=30)

# 3. Start with venv
print('\n=== 3. Start backend ===')
ssh('''
cd /home/ubuntu/sba-backend
source venv/bin/activate
nohup python -m admin.main > /tmp/sba.log 2>&1 &
echo "PID=$!"
''', timeout=15)

# 4. Check
print('\n=== 4. Health check ===')
import time
time.sleep(5)
r = subprocess.run(['ssh', '-i', KEY, '-o', 'StrictHostKeyChecking=no',
        '-o', 'ConnectTimeout=15', '-o', 'UserKnownHostsFile=/dev/null',
        HOST, 'curl -s --max-time 5 http://localhost:9002/api/health'],
        capture_output=True, text=True, timeout=30)
print(f'Health: {r.stdout[:300]}')

# 5. Log
print('\n=== 5. Log ===')
r2 = subprocess.run(['ssh', '-i', KEY, '-o', 'StrictHostKeyChecking=no',
        '-o', 'ConnectTimeout=15', '-o', 'UserKnownHostsFile=/dev/null',
        HOST, 'tail -30 /tmp/sba.log'],
        capture_output=True, text=True, timeout=30)
print(r2.stdout[:500])
if r2.stderr.strip() and 'Warning' not in r2.stderr:
    print('STDERR:', r2.stderr[:200])

print('\n🎉 Updated!')
