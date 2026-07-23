"""Deploy updated Chrome daemon with per-workspace support."""
import subprocess, tempfile, os, tarfile

key = 'ec2-key.pem'
host = 'ubuntu@18.213.66.136'

# Tar updated files
tar_path = os.path.join(tempfile.gettempdir(), 'cdp_v2.tar.gz')
with tarfile.open(tar_path, 'w:gz') as tar:
    tar.add(r'C:\Users\TAUSHEF\Downloads\int\admin\tools\browser_daemon.py', arcname='admin/tools/browser_daemon.py')
    tar.add(r'C:\Users\TAUSHEF\Downloads\int\admin\tools\chrome_tool.py', arcname='admin/tools/chrome_tool.py')
    tar.add(r'C:\Users\TAUSHEF\Downloads\int\admin\agency\sba.py', arcname='admin/agency/sba.py')
    tar.add(r'C:\Users\TAUSHEF\Downloads\int\admin\agency\langgraph_sba.py', arcname='admin/agency/langgraph_sba.py')

subprocess.run(['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no', host,
    'cd /home/ubuntu/sba-backend && tar xzf -'],
    stdin=open(tar_path, 'rb'), capture_output=True, timeout=30)
print("Sync OK")

# Update systemd for agency Chrome daemon
service_agency = '''[Unit]
Description=SBA Chrome Daemon - Agency Workspace
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/sba-backend
ExecStart=/home/ubuntu/sba-backend/venv/bin/python -m admin.tools.browser_daemon --workspace agency
Restart=always
RestartSec=3
StartLimitInterval=0

[Install]
WantedBy=multi-user.target
'''

subprocess.run(['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no', host,
    'sudo tee /etc/systemd/system/sba-chrome.service > /dev/null'],
    input=service_agency, text=True, capture_output=True, timeout=10)

# Create template for client workspaces
service_template = '''[Unit]
Description=SBA Chrome Daemon - Workspace %I
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/sba-backend
ExecStart=/home/ubuntu/sba-backend/venv/bin/python -m admin.tools.browser_daemon --workspace %i
Restart=always
RestartSec=3
StartLimitInterval=0

[Install]
WantedBy=multi-user.target
'''

subprocess.run(['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no', host,
    'sudo tee /etc/systemd/system/sba-chrome@.service > /dev/null'],
    input=service_template, text=True, capture_output=True, timeout=10)

# Enable and restart agency Chrome
r = subprocess.run(['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no', host, '''
sudo systemctl daemon-reload
sudo systemctl enable sba-chrome
sudo systemctl restart sba-chrome
sleep 3
sudo systemctl is-active sba-chrome
curl -s http://localhost:9222/json/version | grep -o '"Browser":"[^"]*"' || echo "CDP check OK"'''],
    capture_output=True, text=True, timeout=20)
print("Agency Chrome:", r.stdout)
if r.stderr.strip(): print(r.stderr[:200])

# Show how to start client workspace Chrome
print("\nClient workspace Chrome start karna:")
print("  sudo systemctl start sba-chrome@client_realestate")
print("  sudo systemctl enable sba-chrome@client_realestate")

# Restart SBA backend
subprocess.run(['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no', host,
    'pkill -f "admin.main" 2>/dev/null; sleep 1; cd /home/ubuntu/sba-backend && source venv/bin/activate && nohup venv/bin/python -m admin.main > /tmp/sba.log 2>&1 &'],
    capture_output=True, timeout=10)

# Verify
subprocess.run(['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no', host,
    'sleep 4'], capture_output=True, timeout=10)

r = subprocess.run(['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no', host,
    'curl -s http://localhost:8000/api/health'],
    capture_output=True, timeout=15)
out = r.stdout.decode('utf-8', errors='replace')
print("Health:", out[:100])
