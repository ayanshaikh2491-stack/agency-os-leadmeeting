"""Sync updated admin files to EC2 and restart."""
import subprocess, tempfile, os, tarfile

key = 'ec2-key.pem'
host = 'ubuntu@18.213.66.136'
local_admin = 'C:/Users/TAUSHEF/Downloads/int/admin'

# Create tar of admin/ (only changed files, but let's just do the whole thing)
tar_path = os.path.join(tempfile.gettempdir(), 'admin_update.tar.gz')
with tarfile.open(tar_path, 'w:gz') as tar:
    tar.add(local_admin, arcname='admin')

# Send via SSH
r = subprocess.run(
    ['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no',
     '-o', 'ConnectTimeout=10', host,
     'cd /home/ubuntu/sba-backend && tar xzf -'],
    stdin=open(tar_path, 'rb'), capture_output=True, text=True, timeout=30
)
print(f"Send: RC={r.returncode} {'OK' if r.returncode==0 else r.stderr[:100]}")

# Restart
script = '#!/bin/bash\nset -e\ncd /home/ubuntu/sba-backend\nsource venv/bin/activate\n'
script += 'pkill -f "admin.main" 2>/dev/null || true\nsleep 1\n'
script += 'nohup venv/bin/python -m admin.main > /tmp/sba.log 2>&1 &\n'
script += 'echo "PID=$!"\nsleep 5\n'
script += 'echo "=== Health ==="\ncurl -s --max-time 5 http://localhost:8000/api/health\n'
script += 'echo ""\necho "=== Via Nginx ==="\ncurl -s http://localhost/api/health\n'

tf = tempfile.NamedTemporaryFile(mode='wb', suffix='.sh', delete=False)
tf.write(script.encode())
tf.close()

subprocess.run(
    ['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no',
     '-o', 'ConnectTimeout=10', host, 'cat > /tmp/restart_sba.sh'],
    stdin=open(tf.name, 'rb'), capture_output=True, timeout=15
)
os.unlink(tf.name)

r = subprocess.run(
    ['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no',
     host, 'bash /tmp/restart_sba.sh'],
    capture_output=True, text=True, timeout=20
)
print(r.stdout[:500])
if r.stderr.strip(): print(f"ERR: {r.stderr[:200]}")
