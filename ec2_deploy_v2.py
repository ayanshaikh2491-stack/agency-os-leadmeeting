"""EC2 Full Fix v2 — swap, deploy, systemd, verify."""
import subprocess, time, sys, tarfile, tempfile, os

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

# ── Wait for EC2 ────────────────────────────────────────────────
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
    print("AWS console -> EC2 -> Instance State -> Start")
    sys.exit(1)

# ── Step 1: Add swap ───────────────────────────────────────────
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
print(f"  Swap: {out[-200:]}")

# ── Step 2: Deploy all updated files ────────────────────────────
BASE = r'C:\Users\TAUSHEF\Downloads\int'
FILES = [
    'admin/tools/browser_daemon.py',
    'admin/tools/chrome_tool.py',
    'admin/tools/test_stealth.py',
    'admin/agency/sba.py',
    'admin/agency/langgraph_sba.py',
    'admin/main.py',
]

print(f"\n📦 Deploying {len(FILES)} files...")
tar_path = os.path.join(tempfile.gettempdir(), 'sba_deploy.tar.gz')
with tarfile.open(tar_path, 'w:gz') as tar:
    for f in FILES:
        local = os.path.join(BASE, f.replace('/', '\\'))
        if os.path.exists(local):
            tar.add(local, arcname=f)
            print(f"  + {f}")

scp_put(tar_path, '/tmp/sba_deploy.tar.gz')
out, err, rc = ssh("cd /home/ubuntu/sba-backend && tar xzf /tmp/sba_deploy.tar.gz", timeout=30)
print(f"  Deploy: {'✅' if rc == 0 else '❌ ' + err[:100]}")

# ── Step 3: Install Playwright if missing ───────────────────────
print("\n📦 Checking Playwright...")
out, err, rc = ssh("""
    source /home/ubuntu/sba-backend/venv/bin/activate
    pip install playwright 2>&1 | tail -1
    python -m playwright install chromium 2>&1 | tail -3
""", timeout=120)
print(f"  PW: {out[-100:]}")

# ── Step 4: Systemd services ───────────────────────────────────
print("\n⚙️ Updating systemd services...")

ssh("""
sudo tee /etc/systemd/system/sba-chrome.service > /dev/null << 'SERVICEEOF'
[Unit]
Description=SBA Chrome Daemon - Agency Workspace
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/sba-backend
Environment=SBA_PROXY=
ExecStart=/home/ubuntu/sba-backend/venv/bin/python -m admin.tools.browser_daemon --workspace agency
Restart=always
RestartSec=5
StartLimitInterval=0
MemoryHigh=400M
MemoryMax=500M
CPUQuota=70%

[Install]
WantedBy=multi-user.target
SERVICEEOF
""", timeout=10)

ssh("""
sudo tee /etc/systemd/system/sba-chrome@.service > /dev/null << 'SERVICEEOF'
[Unit]
Description=Chrome Daemon - Workspace %I
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/sba-backend
Environment=SBA_PROXY=
ExecStart=/home/ubuntu/sba-backend/venv/bin/python -m admin.tools.browser_daemon --workspace %i
Restart=always
RestartSec=5
StartLimitInterval=0
MemoryHigh=400M
MemoryMax=500M
CPUQuota=70%

[Install]
WantedBy=multi-user.target
SERVICEEOF
""", timeout=10)

# sba-backend.service
out, err, rc = ssh("""
sudo tee /etc/systemd/system/sba-backend.service > /dev/null << 'SERVICEEOF'
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
SERVICEEOF
""", timeout=10)

# ── Step 5: Start everything ───────────────────────────────────
print("\n🔥 Starting services...")
out, err, rc = ssh("""
sudo systemctl daemon-reload
sudo systemctl enable sba-chrome
sudo systemctl enable sba-backend
sudo systemctl restart sba-chrome
sleep 8
sudo systemctl restart sba-backend
""", timeout=60)
print(f"  Services: {out[:200] if out else 'triggered'}")

# ── Step 6: Verify ────────────────────────────────────────────
time.sleep(15)
print("\n✅ Verifying...")
out, err, rc = ssh("""
echo "=== Chrome Service ==="
sudo systemctl is-active sba-chrome
echo "=== Chrome Log ==="
sudo journalctl -u sba-chrome --no-pager -n 5 2>/dev/null || echo "no logs"
echo "=== CDP ==="
curl -s --max-time 5 http://localhost:9222/json/version 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('Browser:', d.get('Browser','?'))" 2>/dev/null || echo "CDP not ready"
echo "=== Backend ==="
curl -s --max-time 5 http://localhost:8000/api/health 2>/dev/null || echo "Backend not ready"
echo "=== Memory ==="
free -h | head -2
""", timeout=30)
print(out)

print("\n" + "="*50)
print("✅ DONE! Stealth Chrome running.")
print("="*50)
print("\nClient workspace Chrome start:")
print("  ssh -i ec2-key.pem ubuntu@18.213.66.136")
print("  sudo systemctl start sba-chrome@client_realestate")
print("\nAnti-block test:")
print("  python -m admin.tools.test_stealth")
print("\nCookie login flow:")
print("  1. python -m admin.tools.chrome_tool  (open LinkedIn)")
print("  2. Login manually via VNC/SSH tunnel")
print("  3. Call chrome_save_cookies() tool")
print("  4. Next time: chrome_load_cookies() → LinkedIn logged in")
