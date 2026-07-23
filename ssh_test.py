"""SSH debug test"""
import subprocess, os

key = 'C:/Users/TAUSHEF/Downloads/int/ec2-key.pem'
print('Key exists:', os.path.exists(key))
print('Key size:', os.path.getsize(key) if os.path.exists(key) else 0)

# Try verbose
cmd = ['ssh', '-vvv', '-i', key, '-o', 'StrictHostKeyChecking=no', 
       '-o', 'ConnectTimeout=10', '-o', 'UserKnownHostsFile=/dev/null',
       'ubuntu@18.213.66.136', 'hostname']
r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
print('STDOUT:', r.stdout[:500] if r.stdout else '')
print('STDERR:', r.stderr[:2000] if r.stderr else '')
print('RC:', r.returncode)
