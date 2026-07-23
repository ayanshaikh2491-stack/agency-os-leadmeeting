"""Check EC2 backend status"""
import subprocess, time

KEY = 'ec2-key.pem'
HOST = 'ubuntu@18.213.66.136'
REMOTE = '/home/ubuntu/sba-backend'

def ssh(cmd, timeout=30):
    r = subprocess.run(['ssh', '-i', KEY, '-o', 'StrictHostKeyChecking=no',
                        '-o', 'UserKnownHostsFile=/dev/null', '-o', 'ConnectTimeout=20',
                        HOST, cmd], capture_output=True, timeout=timeout)
    out = r.stdout.decode('utf-8', errors='replace')
    err = r.stderr.decode('utf-8', errors='replace')
    if out.strip(): print(out[:600])
    if err.strip() and 'Warning' not in err:
        for l in err.split('\n')[:3]:
            if l.strip(): print('E:', l[:150])
    return r.returncode

# Retry with 20s gap
for i in range(10):
    print(f'--- Attempt {i+1} ---')
    rc1 = ssh('cat /tmp/sba.log', timeout=25)
    if rc1 == 0:
        print('\n✅ Log fetched!')
        break
    print(f'Waiting 20s...')
    time.sleep(20)
else:
    print('Could not fetch log')

# Also try health directly
print('\n--- Health ---')
for i in range(5):
    rc = ssh('curl -s --max-time 5 http://localhost:9002/api/health', timeout=25)
    if rc == 0:
        break
    print('Waiting 15s...')
    time.sleep(15)
