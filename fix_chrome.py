import subprocess, tempfile, tarfile, os

key = 'ec2-key.pem'
host = 'ubuntu@18.213.66.136'

# Sync just the fixed chrome_tool.py
tar_path = os.path.join(tempfile.gettempdir(), 'fix_tools.tar.gz')
with tarfile.open(tar_path, 'w:gz') as tar:
    tar.add(r'C:\Users\TAUSHEF\Downloads\int\admin\tools\chrome_tool.py', arcname='admin/tools/chrome_tool.py')

subprocess.run(['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no', host,
    'cd /home/ubuntu/sba-backend && tar xzf -'],
    stdin=open(tar_path, 'rb'), capture_output=True, timeout=30)

# Restart
script = '#!/bin/bash\ncd /home/ubuntu/sba-backend\nsource venv/bin/activate\n'
script += 'pkill -f "admin.main" 2>/dev/null; sleep 1\n'
script += 'nohup venv/bin/python -m admin.main > /tmp/sba.log 2>&1 &\nsleep 4\ncurl -s http://localhost:8000/api/health\n'

tf = tempfile.NamedTemporaryFile(mode='wb', suffix='.sh', delete=False)
tf.write(script.encode()); tf.close()

subprocess.run(['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no', host, 'cat > /tmp/restart3.sh'],
    stdin=open(tf.name, 'rb'), capture_output=True, timeout=15)
os.unlink(tf.name)

r = subprocess.run(['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no', host, 'bash /tmp/restart3.sh'],
    capture_output=True, text=True, timeout=20)
print(r.stdout[-300:])
if r.stderr.strip(): print('ERR:', r.stderr[:200])
