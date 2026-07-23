"""Push updated admin + Chrome daemon systemd to EC2."""
import subprocess, tempfile, os, tarfile

key = 'ec2-key.pem'
host = 'ubuntu@18.213.66.136'

# Tar all updated files
tar_path = os.path.join(tempfile.gettempdir(), 'cdp_update.tar.gz')
with tarfile.open(tar_path, 'w:gz') as tar:
    tar.add(r'C:\Users\TAUSHEF\Downloads\int\admin\tools\chrome_tool.py', arcname='admin/tools/chrome_tool.py')
    tar.add(r'C:\Users\TAUSHEF\Downloads\int\admin\tools\browser_daemon.py', arcname='admin/tools/browser_daemon.py')
    tar.add(r'C:\Users\TAUSHEF\Downloads\int\admin\agency\sba.py', arcname='admin/agency/sba.py')
    tar.add(r'C:\Users\TAUSHEF\Downloads\int\admin\agency\langgraph_sba.py', arcname='admin/agency/langgraph_sba.py')

# Sync
subprocess.run(['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no', host,
    'cd /home/ubuntu/sba-backend && tar xzf -'],
    stdin=open(tar_path, 'rb'), capture_output=True, timeout=30)
print("Sync OK")

# Create systemd service for Chrome daemon
service_content = '''[Unit]
Description=SBA Chrome Daemon - persistent browser for SBA agent
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/sba-backend
Environment=SBA_CHROME_CDP_PORT=9222
ExecStart=/home/ubuntu/sba-backend/venv/bin/python -m admin.tools.browser_daemon
Restart=always
RestartSec=3
StartLimitInterval=0

[Install]
WantedBy=multi-user.target
'''

subprocess.run(['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no', host,
    'sudo tee /etc/systemd/system/sba-chrome.service > /dev/null'],
    input=service_content, text=True, capture_output=True, timeout=10)
print("systemd unit created")

# Enable and start Chrome daemon
r = subprocess.run(['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no', host,
    'sudo systemctl daemon-reload && sudo systemctl enable sba-chrome && sudo systemctl restart sba-chrome && sleep 4 && sudo systemctl status sba-chrome --no-pager | head -15'],
    capture_output=True, text=True, timeout=20)
print("Status:", r.stdout)
if r.stderr.strip(): print("ERR:", r.stderr[:300])

# Restart SBA backend
subprocess.run(['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no', host,
    'pkill -f "admin.main" 2>/dev/null; sleep 1; cd /home/ubuntu/sba-backend && source venv/bin/activate && nohup venv/bin/python -m admin.main > /tmp/sba.log 2>&1 &'],
    capture_output=True, timeout=10)
print("SBA restarted")

# Final check
r = subprocess.run(['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no', host,
    'sleep 5 && curl -s http://localhost:8000/api/health'],
    capture_output=True, text=True, timeout=15)
print("Health:", r.stdout)
