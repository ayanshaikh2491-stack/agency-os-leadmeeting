"""Check EC2"""
import subprocess, time
time.sleep(3)
r = subprocess.run(['ssh','-i','ec2-key.pem','-o','StrictHostKeyChecking=no','-o','ConnectTimeout=15','-o','UserKnownHostsFile=/dev/null','ubuntu@18.213.66.136','hostname'], capture_output=True, text=True, timeout=25)
print('OUT:', r.stdout[:100])
print('RC:', r.returncode)
