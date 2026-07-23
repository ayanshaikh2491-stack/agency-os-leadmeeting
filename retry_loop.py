"""Check EC2 port 22 - with retries"""
import subprocess, time

KEY = 'ec2-key.pem'
HOST = 'ubuntu@18.213.66.136'

def try_ssh():
    r = subprocess.run(['ssh', '-i', KEY, '-o', 'StrictHostKeyChecking=no',
                        '-o', 'ConnectTimeout=20', '-o', 'UserKnownHostsFile=/dev/null',
                        HOST, 'hostname'],
                       capture_output=True, text=True, timeout=30)
    return r.returncode, r.stdout[:100]

# Retry loop with increasing delays
for attempt in range(5):
    print(f'Attempt {attempt+1}...')
    rc, out = try_ssh()
    if rc == 0:
        print(f'✅ Connected! {out}')
        break
    else:
        print(f'❌ Failed (rc={rc}), waiting 30s...')
        time.sleep(30)
else:
    print('All attempts failed. EC2 may be throttling us.')
