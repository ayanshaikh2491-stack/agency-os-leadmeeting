"""Wait 30s then check EC2"""
import subprocess, os, time

time.sleep(30)

KEY = 'C:/Users/TAUSHEF/Downloads/int/ec2-key.pem'
cmd = ['ssh', '-vvv', '-i', KEY, '-o', 'StrictHostKeyChecking=no',
       '-o', 'ConnectTimeout=10', '-o', 'UserKnownHostsFile=/dev/null',
       'ubuntu@18.213.66.136', 'hostname']
r = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
print('STDOUT:', r.stdout[:200])
print('STDERR_TAIL:', r.stderr[-500:])
print('RC:', r.returncode)
