"""Check EC2 backend error"""
import subprocess

KEY = 'ec2-key.pem'
HOST = 'ubuntu@18.213.66.136'

for cmd, name in [
    ('cat /tmp/sba.log', 'Full log'),
    ('ls -la /home/ubuntu/sba-backend/admin/', 'Admin dir'),
    ('ls -la /home/ubuntu/sba-backend/admin/agency/', 'Agency dir'),
]:
    r = subprocess.run(['ssh', '-i', KEY, '-o', 'StrictHostKeyChecking=no',
                        '-o', 'UserKnownHostsFile=/dev/null', '-o', 'ConnectTimeout=20',
                        HOST, cmd], capture_output=True, text=True, timeout=30)
    print(f'=== {name} ===')
    if r.stdout.strip(): print(r.stdout[:800])
    if r.stderr.strip() and 'Warning' not in r.stderr: print('E:', r.stderr[:200])
    print()
