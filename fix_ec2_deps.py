"""Fix EC2 - install all deps"""
import subprocess, time

KEY = 'ec2-key.pem'
HOST = 'ubuntu@18.213.66.136'
V = '/home/ubuntu/sba-backend/venv'

def try_ssh(cmd, timeout=30):
    r = subprocess.run(['ssh', '-i', KEY, '-o', 'StrictHostKeyChecking=no',
                        '-o', 'UserKnownHostsFile=/dev/null', '-o', 'ConnectTimeout=20',
                        HOST, cmd], capture_output=True, timeout=timeout)
    out = r.stdout.decode('utf-8', errors='replace')
    err = r.stderr.decode('utf-8', errors='replace')
    if out.strip(): print(out[:500])
    if err.strip() and 'Warning' not in err:
        for l in err.split('\n')[:3]:
            if l.strip(): print('E:', l[:150])
    return r.returncode

# Retry loop
for attempt in range(5):
    print(f'Attempt {attempt+1}: installing deps...')
    rc = try_ssh(f'{V}/bin/pip install openai langgraph langchain langchain-openai sqlalchemy asyncpg python-dotenv 2>&1 | tail -5', timeout=180)
    if rc == 0:
        print('✅ Installed!')
        break
    print(f'Failed, waiting 30s...')
    time.sleep(30)
else:
    print('All attempts failed')
    exit(1)

# Now check if backend starts
print('\n=== Starting backend ===')
try_ssh(f'cd /home/ubuntu/sba-backend; pkill -f admin.main 2>/dev/null; PYTHONPATH=/home/ubuntu/sba-backend nohup {V}/bin/python -m admin.main > /tmp/sba.log 2>&1 &', timeout=30)

time.sleep(6)

print('\n=== Health ===')
try_ssh('curl -s --max-time 5 http://localhost:9002/api/health', timeout=30)

print('\n=== Log ===')
try_ssh('tail -20 /tmp/sba.log', timeout=30)

print('\n🎉 Done!')
