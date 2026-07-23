import subprocess, os

ssh_dir = 'C:/Users/TAUSHEF/.ssh'
keys = [
    'agency-ec2-key.pem',
    'agency-ec2-key-fixed.pem',
    'agency-ec2.pem',
    'agency-backend-key-v2.pem',
    'agency-backend-key-20260521.pem',
    'ec2-deploy-key',
    'deploy-key-20260520.pem',
]

for key in keys:
    path = os.path.join(ssh_dir, key)
    if not os.path.exists(path):
        print('MISS ' + key)
        continue
    try:
        cmd = ['ssh', '-i', path, '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=5',
               'ubuntu@18.213.66.136', 'echo OK && hostname']
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            print('OK   ' + key + ' -> ' + r.stdout.strip())
        else:
            print('FAIL ' + key + ' -> ' + r.stderr.strip()[:60])
    except subprocess.TimeoutExpired:
        print('TIME ' + key)
    except Exception as e:
        print('ERR  ' + key + ' -> ' + str(e)[:60])
