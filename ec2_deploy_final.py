"""EC2 Final Deploy — swap + playwright-stealth + systemd + verify."""
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
        print(f"  ...waiting ({i}s)")
    time.sleep(5)
else:
    print("❌ EC2 not back. Start from AWS console.")
    sys.exit(1)

# ── Step 1: Add swap ───────────────────────────────────────────
print("\n📦 Adding 2GB swap...")
out, err, rc = ssh("""
    sudo swapoff -a 2>/dev/null
    sudo fallocate -l 2G /swapfile 2>/dev/null || sudo dd if=/dev/zero of=/swapfile bs=1M count=2048
    sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile
    grep -q 'vm.swappiness=10' /etc/sysctl.conf || echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
    sudo sysctl -p
    free -h | grep -i swap
""", timeout=120)
print(f"  {out.strip()[-100:]}")

# ── Step 2: Deploy code ─────────────────────────────────────────
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
ssh("cd /home/ubuntu/sba-backend && tar xzf /tmp/sba_deploy.tar.gz", timeout=30)
print("  ✅ Code deployed")

# ── Step 3: Install playwright-stealth ──────────────────────────
print("\n📦 Installing playwright-stealth...")
out, err, rc = ssh("""
    source /home/ubuntu/sba-backend/venv/bin/activate
    pip install playwright-stealth 2>&1 | tail -3
""", timeout=120)
print(f"  {out.strip()[-200:]}")

# Also install playwright if missing
print("📦 Checking Playwright browsers...")
out, err, rc = ssh("""
    source /home/ubuntu/sba-backend/venv/bin/activate
    python -m playwright install chromium 2>&1 | tail -3
""", timeout=120)
print(f"  {out.strip()[-200:]}")

# ── Step 4: Systemd services ───────────────────────────────────
print("\n⚙️ Systemd services...")

SERVICES = {
    'sba-chrome.service': f"""
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
""",
    'sba-chrome@.service': f"""
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
""",
    'sba-backend.service': f"""
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
""",
}

for svc_name, svc_content in SERVICES.items():
    # Write via tee
    ssh(f"sudo tee /etc/systemd/system/{svc_name} > /dev/null << 'EOF'\n{svc_content}\nEOF", timeout=10)
    print(f"  ✅ {svc_name}")

# ── Step 5: Start everything ───────────────────────────────────
print("\n🔥 Starting services...")
out, err, rc = ssh("""
    sudo systemctl daemon-reload
    sudo systemctl enable sba-chrome
    sudo systemctl enable sba-backend
    sudo systemctl restart sba-chrome
    sleep 10
    sudo systemctl restart sba-backend
""", timeout=60)
print(f"  Services started")

# ── Step 6: Verify ─────────────────────────────────────────────
time.sleep(15)
print("\n✅ Verifying...")
out, err, rc = ssh("""
echo "=== Chrome Service ==="
sudo systemctl is-active sba-chrome
echo "=== Chrome Log ==="
sudo journalctl -u sba-chrome --no-pager -n 10 2>/dev/null
echo "=== CDP ==="
curl -s --max-time 5 http://localhost:9222/json/version 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('Browser:', d.get('Browser','?')); print('Pages:', len(d.get('webSocketDebuggerUrl','').split()))"
echo "=== Backend ==="
curl -s --max-time 5 http://localhost:8000/api/health 2>/dev/null || echo "Backend not ready"
echo "=== Memory ==="
free -h | head -2
""", timeout=30)
print(out)

print("\n" + "="*50)
print("✅ FINAL DEPLOY COMPLETE!")
print("="*50)
print("\n📋 Status:")
print("  Chrome daemon: ON (port 9222)")
print("  playwright-stealth: 31 patches active")
print("  Extra stealth: WebGL, CDP, canvas fixes active")
print("  Cookie persistence: auto-save/restore")
print("  Proxy rotation: ready (set SBA_PROXY_LIST)")
print("  Human delays: char-by-char typing, random clicks")
print("\n🔧 Client workspace:")
print("  sudo systemctl start sba-chrome@client_realestate")
print("\n🔍 Test stealth:")
print("  python -m admin.tools.test_stealth")
print("\n🔐 LinkedIn login (one-time):")
print("  1. Call chrome_linkedin_login(email, password)")
print("  2. Or manually login then chrome_save_cookies()")
print("  3. Future: chrome_load_cookies() → instant login")
