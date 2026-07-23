"""Deploy EC2 - separate steps with retries"""
import subprocess, os, tarfile, tempfile, time

KEY = 'ec2-key.pem'
HOST = 'ubuntu@18.213.66.136'
REMOTE = '/home/ubuntu/sba-backend'

def ssh(cmd, timeout=30):
    full = ['ssh', '-i', KEY, '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null', '-o', 'ConnectTimeout=20',
            HOST, cmd]
    r = subprocess.run(full, capture_output=True, text=True, timeout=timeout)
    if r.stdout.strip(): print(r.stdout[:400])
    if r.stderr.strip() and 'Warning' not in r.stderr:
        for l in r.stderr.split('\n')[:3]:
            if l.strip(): print('E:', l[:150])
    return r.returncode

# 1. Kill old
print('=== 1. Kill old ===')
ssh('pkill -f admin.main 2>/dev/null; echo done', timeout=30)

# 2. Send tar via pipe (separate connection)
print('\n=== 2. Send tar ===')
tar_path = os.path.join(tempfile.gettempdir(), 'sba_deploy3.tar.gz')
with tarfile.open(tar_path, 'w:gz') as tar:
    tar.add('admin', arcname='admin')
print(f'Tar: {os.path.getsize(tar_path)/1024:.0f} KB')

send_cmd = ['ssh', '-i', KEY, '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null', '-o', 'ConnectTimeout=20',
            HOST, f'cd {REMOTE} && tar xzf -']
with open(tar_path, 'rb') as f:
    r = subprocess.run(send_cmd, stdin=f, capture_output=True, text=True, timeout=60)
    print('Sent:', 'OK' if r.returncode == 0 else 'FAIL')
    if r.stderr.strip() and 'Warning' not in r.stderr:
        print('E:', r.stderr[:200])

# 3. Verify files
print('\n=== 3. Verify ===')
ssh(f'ls -la {REMOTE}/admin/main.py', timeout=30)

# 4. Check log for error
print('\n=== 4. Log (old) ===')
ssh(f'tail -10 /tmp/sba.log', timeout=30)

# 5. Start with proper PYTHONPATH
print('\n=== 5. Start ===')
ssh(f'cd {REMOTE} && PYTHONPATH={REMOTE} nohup {REMOTE}/venv/bin/python -m admin.main > /tmp/sba.log 2>&1 & echo started', timeout=30)

# 6. Health
print('\n=== 6. Health ===')
time.sleep(6)
ssh(f'curl -s --max-time 5 http://localhost:9002/api/health', timeout=30)

# 7. Log
print('\n=== 7. Log ===')
ssh(f'tail -15 /tmp/sba.log', timeout=30)

print('\n🎉 Done!')
