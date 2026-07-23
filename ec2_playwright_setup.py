"""Install Playwright on EC2 + push updated chrome_tool.py."""
import subprocess, tempfile, os, tarfile

key = 'ec2-key.pem'
host = 'ubuntu@18.213.66.136'

# Step 1: Install Playwright on EC2
script = '#!/bin/bash\nset -e\ncd /home/ubuntu/sba-backend\nsource venv/bin/activate\n'
script += 'echo "=== Installing playwright === "\n'
script += 'pip install playwright 2>&1 | tail -3\n'
script += 'echo "=== Installing Chromium browser === "\n'
script += 'python -m playwright install chromium 2>&1 | tail -5\n'
script += 'echo "=== DONE === "\n'

tf = tempfile.NamedTemporaryFile(mode='wb', suffix='.sh', delete=False)
tf.write(script.encode())
tf.close()

subprocess.run(
    ['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no',
     '-o', 'ConnectTimeout=10', host, 'cat > /tmp/install_pw.sh'],
    stdin=open(tf.name, 'rb'), capture_output=True, timeout=15
)
os.unlink(tf.name)

print("Installing Playwright on EC2...")
r = subprocess.run(
    ['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no',
     '-o', 'ConnectTimeout=10', host, 'bash /tmp/install_pw.sh'],
    capture_output=True, text=True, timeout=180
)
print(r.stdout[-300:])
if r.stderr.strip(): print(f"ERR: {r.stderr[:200]}")

# Also add playwright to requirements.txt
req_path = r'C:\Users\TAUSHEF\Downloads\int\admin\requirements.txt'
with open(req_path) as f:
    reqs = f.read()
if 'playwright' not in reqs:
    with open(req_path, 'a') as f:
        f.write('\nplaywright>=1.40.0\n')

# Step 2: Sync updated admin files to EC2
print("\nSyncing updated files to EC2...")
tar_path = os.path.join(tempfile.gettempdir(), 'admin_sync.tar.gz')
with tarfile.open(tar_path, 'w:gz') as tar:
    tar.add(r'C:\Users\TAUSHEF\Downloads\int\admin', arcname='admin')

r = subprocess.run(
    ['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no',
     '-o', 'ConnectTimeout=10', host,
     'cd /home/ubuntu/sba-backend && tar xzf -'],
    stdin=open(tar_path, 'rb'), capture_output=True, timeout=30
)
print(f"Sync: {'OK' if r.returncode==0 else r.stderr[:100]}")

# Step 3: Restart backend
script2 = '#!/bin/bash\nset -e\ncd /home/ubuntu/sba-backend\nsource venv/bin/activate\n'
script2 += 'pkill -f "admin.main" 2>/dev/null || true\nsleep 1\n'
script2 += 'nohup venv/bin/python -m admin.main > /tmp/sba.log 2>&1 &\n'
script2 += 'sleep 5\ncurl -s http://localhost:8000/api/health\n'

tf2 = tempfile.NamedTemporaryFile(mode='wb', suffix='.sh', delete=False)
tf2.write(script2.encode())
tf2.close()

subprocess.run(
    ['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no',
     '-o', 'ConnectTimeout=10', host, 'cat > /tmp/restart2.sh'],
    stdin=open(tf2.name, 'rb'), capture_output=True, timeout=15
)
os.unlink(tf2.name)

r = subprocess.run(
    ['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no',
     host, 'bash /tmp/restart2.sh'],
    capture_output=True, text=True, timeout=20
)
print(f"Restart: {r.stdout[:200]}")
print("✅ Done! Playwright + updated prompt deployed.")
