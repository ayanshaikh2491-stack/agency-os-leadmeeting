"""Test SSH with verbose output"""
import subprocess, os

key = 'C:/Users/TAUSHEF/Downloads/int/ec2-key.pem'

cmd = ['ssh', '-vvv', '-i', key, 
       '-o', 'StrictHostKeyChecking=no', 
       '-o', 'ConnectTimeout=20', 
       '-o', 'UserKnownHostsFile=/dev/null',
       'ubuntu@18.213.66.136', 'hostname']
r = subprocess.run(cmd, capture_output=True, text=True, timeout=35)
print('STDOUT:', r.stdout[:500])
print('STDERR_END:', r.stderr[-1000:])
print('RC:', r.returncode)
