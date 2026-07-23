"""Fix SBA backend on EC2 - standalone"""
import subprocess
import time

KEY = 'C:/Users/TAUSHEF/Downloads/int/ec2-key.pem'
BASE = ['ssh', '-i', KEY, '-o', 'StrictHostKeyChecking=no',
        '-o', 'ConnectTimeout=15', '-o', 'UserKnownHostsFile=/dev/null',
        'ubuntu@18.213.66.136']

def run(cmd, timeout=90):
    r = subprocess.run(BASE + [cmd], capture_output=True, timeout=timeout)
    o = r.stdout.decode('utf-8', errors='replace').strip()
    e = r.stderr.decode('utf-8', errors='replace').strip()
    if o: print(o)
    if e and 'Warning' not in e:
        for line in e.split('\n')[:5]:
            print('E:', line)
    return r.returncode, o

# Step 1: Kill old process
print('=== Kill old ===')
run('pkill -f admin.main 2>/dev/null; echo killed')

# Step 2: Check venv exists
print('=== Check venv ===')
rc, o = run('ls /home/ubuntu/sba-backend/venv/bin/python 2>/dev/null && echo FOUND || echo MISSING')
if 'MISSING' in o:
    print('Creating venv...')
    run('cd /home/ubuntu/sba-backend && python3 -m venv venv', timeout=30)
    run('/home/ubuntu/sba-backend/venv/bin/pip install fastapi uvicorn httpx python-multipart pydantic 2>&1 | tail -3', timeout=180)

# Step 3: List files
print('=== Files ===')
run('find /home/ubuntu/sba-backend/admin -name "*.py" | head -20')

# Step 4: Start with PYTHONPATH
print('=== Start ===')
run('cd /home/ubuntu/sba-backend && PYTHONPATH=/home/ubuntu/sba-backend nohup venv/bin/python -m admin.main > /tmp/sba.log 2>&1 & echo STARTED')

# Step 5: Wait and health
print('=== Wait ===')
time.sleep(6)
print('=== Health ===')
rc, o = run('curl -s --max-time 5 http://localhost:9002/api/health')
print('Health:', o[:500])

# Step 6: Log
print('=== Log ===')
rc, o = run('tail -30 /tmp/sba.log')
print(o[:1000])

print('=== DONE ===')
