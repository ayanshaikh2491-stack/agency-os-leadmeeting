"""EC2 Step 1: Fix backend - stable approach with single connection"""
import subprocess, time, os, tarfile, tempfile

KEY = 'ec2-key.pem'
HOST = 'ubuntu@18.213.66.136'
REMOTE = '/home/ubuntu/sba-backend'

def run_ssh(cmd, timeout=30):
    """Single SSH call - no retry logic inside"""
    r = subprocess.run(['ssh', '-i', KEY, '-o', 'StrictHostKeyChecking=no',
                        '-o', 'UserKnownHostsFile=/dev/null', '-o', 'ConnectTimeout=20',
                        HOST, cmd], capture_output=True, timeout=timeout)
    out = r.stdout.decode('utf-8', errors='replace')
    err = r.stderr.decode('utf-8', errors='replace')
    return out, err, r.returncode

# Step 1: Check current log
print('=== 1. Current log ===')
out, err, rc = run_ssh('tail -30 /tmp/sba.log', timeout=25)
print(out[:600])
if err and 'Warning' not in err: print('ERR:', err[:200])

# Step 2: Try starting manually to see error
print('\n=== 2. Manual start to see error ===')
out, err, rc = run_ssh(
    f'cd {REMOTE} && PYTHONPATH={REMOTE} {REMOTE}/venv/bin/python -c "from admin.main import app; print(\'IMPORT OK\')"', 
    timeout=30
)
print(out[:400])
if err and 'Warning' not in err: print('ERR:', err[:200])

# Step 3: Fix and restart
print('\n=== 3. Fix and restart ===')
start_cmd = f'cd {REMOTE}; pkill -f admin.main 2>/dev/null; PYTHONPATH={REMOTE} nohup {REMOTE}/venv/bin/python -m admin.main > /tmp/sba.log 2>&1 & echo DONE'
out, err, rc = run_ssh(start_cmd, timeout=30)
print(out[:200])
if err and 'Warning' not in err: print('ERR:', err[:200])

# Step 4: Wait and health
print('\n=== 4. Health check ===')
time.sleep(6)
out, err, rc = run_ssh('curl -s --max-time 5 http://localhost:9002/api/health', timeout=25)
print('Health:', out[:200])

# Step 5: Final log
print('\n=== 5. Final log ===')
out, err, rc = run_ssh('tail -20 /tmp/sba.log', timeout=25)
print(out[:500])

print('\n🎉 EC2 Step 1 done!')
