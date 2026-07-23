"""EC2 Full Fix — swap, auto-recovery, ab service deploy."""
import subprocess, time, sys

key = 'ec2-key.pem'
host = 'ubuntu@18.213.66.136'

def ssh(cmd, timeout=30):
    try:
        r = subprocess.run(['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no',
            '-o', 'ConnectTimeout=5', '-o', 'ServerAliveInterval=3', host, cmd],
            capture_output=True, text=True, timeout=timeout)
        return r.stdout, r.stderr, r.returncode
    except Exception as e:
        return "", str(e), -1

def scp_put(local, remote):
    subprocess.run(['scp', '-i', key, '-o', 'StrictHostKeyChecking=no',
        '-o', 'ConnectTimeout=5', local, f'{host}:{remote}'],
        capture_output=True, timeout=30)

# Wait for EC2 to come up
print("⏳ Waiting for EC2 to come back...")
for i in range(1, 121):
    out, err, rc = ssh("echo up")
    if rc == 0:
        print(f"✅ EC2 UP at attempt {i}")
        break
    if i % 10 == 0:
        print(f"  ...still waiting ({i}s)")
    time.sleep(5)
else:
    print("❌ EC2 didn't come back after 10 min")
    print("Manual restart karo AWS console me, phir yeh script run karo")
    sys.exit(1)

# ── Step 1: Add swap ──────────────────────────────────────────
print("\n📦 Adding 2GB swap...")
out, err, rc = ssh("""
    sudo swapoff -a 2>/dev/null
    sudo fallocate -l 2G /swapfile 2>/dev/null || sudo dd if=/dev/zero of=/swapfile bs=1M count=2048
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
    sudo sysctl -p
    free -h | grep Swap
""", timeout=120)
print(f"  {out[-200:]}")
if err.strip(): print(f"  err: {err[:200]}")

# ── Step 2: Deploy updated code ───────────────────────────────
print("\n📦 Deploying updated code...")
import tarfile, tempfile, os
tar_path = os.path.join(tempfile.gettempdir(), 'full_deploy.tar.gz')
with tarfile.open(tar_path, 'w:gz') as tar:
    tar.add(r'C:\Users\TAUSHEF\Downloads\int\admin\tools\browser_daemon.py', arcname='admin/tools/browser_daemon.py')
    tar.add(r'C:\Users\TAUSHEF\Downloads\int\admin\tools\chrome_tool.py', arcname='admin/tools/chrome_tool.py')
    tar.add(r'C:\Users\TAUSHEF\Downloads\int\admin\agency\sba.py', arcname='admin/agency/sba.py')
    tar.add(r'C:\Users\TAUSHEF\Downloads\int\admin\agency\langgraph_sba.py', arcname='admin/agency/langgraph_sba.py')
    tar.add(r'C:\Users\TAUSHEF\Downloads\int\admin\main.py', arcname='admin/main.py')

scp_put(tar_path, '/tmp/deploy.tar.gz')
out, err, rc = ssh("cd /home/ubuntu/sba-backend && tar xzf /tmp/deploy.tar.gz", timeout=30)
print(f"  Sync: {'OK' if rc == 0 else err[:100]}")

# ── Step 3: Systemd services ──────────────────────────────────
print("\n⚙️ Setting up systemd services...")

# sba-chrome.service (agency)
out, err, rc = ssh("""
sudo tee /etc/systemd/system/sba-chrome.service > /dev/null << 'EOF'
[Unit]
Description=SBA Chrome Daemon - Agency Workspace
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/sba-backend
ExecStart=/home/ubuntu/sba-backend/venv/bin/python -m admin.tools.browser_daemon --workspace agency
Restart=always
RestartSec=5
StartLimitInterval=0
MemoryHigh=400M
MemoryMax=500M

[Install]
WantedBy=multi-user.target
EOF
""", timeout=10)

# Template for client workspaces
out, err, rc = ssh("""
sudo tee /etc/systemd/system/sba-chrome@.service > /dev/null << 'EOF'
[Unit]
Description=Chrome Daemon - Workspace %I
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/sba-backend
ExecStart=/home/ubuntu/sba-backend/venv/bin/python -m admin.tools.browser_daemon --workspace %i
Restart=always
RestartSec=5
StartLimitInterval=0
MemoryHigh=400M
MemoryMax=500M

[Install]
WantedBy=multi-user.target
EOF
""", timeout=10)

# sba-backend.service
out, err, rc = ssh("""
sudo tee /etc/systemd/system/sba-backend.service > /dev/null << 'EOF'
[Unit]
Description=SBA Backend
After=network.target sba-chrome.service
Wants=sba-chrome.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/sba-backend
ExecStart=/home/ubuntu/sba-backend/venv/bin/python -m admin.main
Restart=always
RestartSec=5
StartLimitInterval=0

[Install]
WantedBy=multi-user.target
EOF
""", timeout=10)

# ── Step 4: Enable & start everything ─────────────────────────
print("\n🔥 Starting services...")
out, err, rc = ssh("""
sudo systemctl daemon-reload
sudo systemctl enable sba-chrome
sudo systemctl enable sba-backend
sudo systemctl restart sba-chrome
sleep 5
sudo systemctl restart sba-backend
""", timeout=30)

# ── Step 5: Verify ────────────────────────────────────────────
time.sleep(10)
print("\n✅ Verifying...")
out, err, rc = ssh("""
echo "=== Chrome ==="
sudo systemctl is-active sba-chrome
echo "=== CDP ==="
curl -s --max-time 5 http://localhost:9222/json/version | grep -o '"Browser":"[^"]*"'
echo "=== Backend ==="
curl -s --max-time 5 http://localhost:8000/api/health
echo "=== Memory ==="
free -h | head -2
""", timeout=20)
print(out)
if err.strip(): print(f"  err: {err[:200]}")

print("\n✅ All set! Client workspace Chrome start karna:")
print("   sudo systemctl start sba-chrome@client_realestate")
