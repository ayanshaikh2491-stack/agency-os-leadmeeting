"""Fix SBA on EC2 - use direct venv paths, more reliable"""
import subprocess, os

KEY = 'C:/Users/TAUSHEF/Downloads/int/ec2-key.pem'
V = '/home/ubuntu/sba-backend/venv'
BASE = ['ssh', '-i', KEY, '-o', 'StrictHostKeyChecking=no',
        '-o', 'ConnectTimeout=15', '-o', 'UserKnownHostsFile=/dev/null',
        'ubuntu@18.213.66.136']

def run(cmd, timeout=120):
    r = subprocess.run(BASE + [cmd], capture_output=True, timeout=timeout)
    out = r.stdout.decode('utf-8', errors='replace')
    err = r.stderr.decode('utf-8', errors='replace')
    if out.strip(): print(out[:600])
    if err.strip() and 'Warning' not in err and 'established' not in err:
        print('ERR:', err[:300])
    return r.returncode

# 1. Create venv
print('=== 1. Create venv ===')
run('cd /home/ubuntu/sba-backend && python3 -m venv venv', timeout=30)

# 2. Install deps
print('\n=== 2. Install deps ===')
run(f'{V}/bin/pip install fastapi uvicorn httpx python-multipart pydantic 2>&1 | tail -3', timeout=180)

# 3. Test import
print('\n=== 3. Test import ===')
run(f'cd /home/ubuntu/sba-backend && {V}/bin/python -c "import sys; sys.path.insert(0,\".\"); from admin.api.models.schemas import HealthResponse; print(\"IMPORT OK\")"', timeout=30)

# 4. Kill old + restart
print('\n=== 4. Restart backend ===')
run('pkill -f "admin.main" 2>/dev/null; ' + 
    f'cd /home/ubuntu/sba-backend && nohup {V}/bin/python -m admin.main > /tmp/sba.log 2>&1 &', timeout=15)

# 5. Wait + health
print('\n=== 5. Health check ===')
import time
time.sleep(4)
r = subprocess.run(BASE + ['curl -s --max-time 5 http://localhost:9002/api/health'],
                   capture_output=True, timeout=30)
print('Health:', r.stdout.decode('utf-8', errors='replace')[:300])

# 6. Log
print('\n=== 6. Log ===')
r = subprocess.run(BASE + ['tail -25 /tmp/sba.log'],
                   capture_output=True, timeout=30)
print(r.stdout.decode('utf-8', errors='replace')[:600])

print('\n🎉 Done!')
