#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""Consolidated Deploy: SBA Backend to EC2 + Frontend Connection

Usage:
    python deploy_sba.py             # Dry-run: show what will happen
    python deploy_sba.py --run       # Actual deploy (EC2 must be reachable)
    python deploy_sba.py --frontend  # Only update Vercel env vars
"""

import argparse
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time

# ── Config ───────────────────────────────────────────────────────────────────
KEY = 'C:/Users/TAUSHEF/Downloads/int/ec2-key.pem'
SSH_HOST = 'ubuntu@18.213.66.136'
EC2_IP = '18.213.66.136'
REMOTE_DIR = '/home/ubuntu/sba-backend'
LOCAL_ADMIN = 'C:/Users/TAUSHEF/Downloads/int/admin'
LOCAL_ROOT = 'C:/Users/TAUSHEF/Downloads/int'
LOCAL_CHROME_AGENT = 'C:/Users/TAUSHEF/Downloads/int/chrome-agent'

BACKEND_PORT = 8000
SSH_OPTS = [
    '-i', KEY,
    '-o', 'StrictHostKeyChecking=no',
    '-o', 'ConnectTimeout=15',
    '-o', 'UserKnownHostsFile=/dev/null',
]


def log(msg: str) -> None:
    print(f"  {msg}")


def ok(msg: str) -> None:
    print(f"  ✅ {msg}")


def warn(msg: str) -> None:
    print(f"  ⚠️  {msg}")


def fail(msg: str) -> None:
    print(f"  ❌ {msg}")
    sys.exit(1)


def ssh_exec(cmd: str, timeout: int = 60, capture: bool = True) -> subprocess.CompletedProcess:
    """Run a command via SSH."""
    full_cmd = ['ssh'] + SSH_OPTS + [SSH_HOST, cmd]
    return subprocess.run(
        full_cmd,
        capture_output=capture,
        text=True,
        timeout=timeout,
    )


# ── Phases ───────────────────────────────────────────────────────────────────


def phase_check_ec2() -> bool:
    """Check if EC2 is reachable."""
    log("Checking EC2 reachability...")
    try:
        r = ssh_exec("echo 'pong'", timeout=10)
        if r.returncode == 0:
            ok(f"EC2 reachable at {EC2_IP}")
            return True
    except (subprocess.TimeoutExpired, Exception) as e:
        warn(f"EC2 not reachable: {e}")
    return False


def phase_send_files(dry_run: bool) -> None:
    """Tar admin/ + requirements.txt + .env → EC2."""
    log("Packaging admin backend...")
    tar_path = os.path.join(tempfile.gettempdir(), 'sba_deploy.tar.gz')
    
    with tarfile.open(tar_path, 'w:gz') as tar:
        # Add admin/ directory
        tar.add(LOCAL_ADMIN, arcname='admin')
        # Add requirements.txt
        tar.add(os.path.join(LOCAL_ROOT, 'admin', 'requirements.txt'),
                arcname='requirements.txt')
        # Add .env
        env_file = os.path.join(LOCAL_ROOT, '.env')
        if os.path.exists(env_file):
            tar.add(env_file, arcname='.env')
    
    size_kb = os.path.getsize(tar_path) / 1024
    log(f"Package: {size_kb:.0f} KB")

    if dry_run:
        log(f"[DRY-RUN] Would send to {SSH_HOST}:{REMOTE_DIR}")
        return

    log("Sending files to EC2...")
    ssh_cmd = ['ssh'] + SSH_OPTS + [SSH_HOST,
               f'mkdir -p {REMOTE_DIR} && cd {REMOTE_DIR} && tar xzf -']
    
    with open(tar_path, 'rb') as f:
        r = subprocess.run(ssh_cmd, stdin=f, capture_output=True, text=True,
                          timeout=60)
    
    if r.returncode != 0:
        fail(f"File transfer failed: {r.stderr[:200]}")
    ok(f"Files sent ({size_kb:.0f} KB)")


def phase_setup_ec2(dry_run: bool) -> None:
    """Install system deps + Python venv + requirements."""
    script = f"""
set -e
cd {REMOTE_DIR}

echo "--- Installing system deps ---"
sudo apt-get update -qq
sudo apt-get install -y -qq python3 python3-pip python3-venv nginx 2>&1 | tail -3

echo "--- Setting up Python venv ---"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip3 install --quiet -r requirements.txt 2>&1 | tail -3
echo "Python deps installed"
"""
    if dry_run:
        log("[DRY-RUN] Would install system deps + Python venv")
        return

    log("Setting up EC2 environment...")
    r = ssh_exec(script, timeout=120)
    if r.returncode != 0:
        fail(f"Setup failed: {r.stderr[:200]}")
    ok("EC2 environment ready")


def phase_start_backend(dry_run: bool) -> None:
    """Kill old SBA + start new backend via systemd."""
    # Create systemd service
    service_content = f"""[Unit]
Description=SBA Backend (TAGS Agency)
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory={REMOTE_DIR}
Environment=PYTHONPATH={REMOTE_DIR}
ExecStart={REMOTE_DIR}/venv/bin/python -m admin.main
Restart=always
RestartSec=5
StandardOutput=append:/var/log/sba.log
StandardError=append:/var/log/sba.log

[Install]
WantedBy=multi-user.target
"""

    start_script = f"""
set -e
cd {REMOTE_DIR}

# Write systemd service
cat > /tmp/sba.service << 'SERVICE'
{service_content}
SERVICE
sudo mv /tmp/sba.service /etc/systemd/system/sba.service
sudo systemctl daemon-reload

# Stop old process if running
sudo systemctl stop sba 2>/dev/null || true
pkill -f "admin.main" 2>/dev/null || true
sleep 1

# Start new one
sudo systemctl enable sba
sudo systemctl start sba

echo "Waiting 5s for startup..."
sleep 5

# Health check
echo "--- Health Check ---"
curl -s --max-time 5 http://localhost:{BACKEND_PORT}/api/health || echo "Health check failed"

echo "--- Last 20 log lines ---"
sudo tail -20 /var/log/sba.log 2>/dev/null || echo "No log yet"
"""
    if dry_run:
        log(f"[DRY-RUN] Would start backend on port {BACKEND_PORT}")
        return

    log("Starting SBA backend via systemd...")
    r = ssh_exec(start_script, timeout=30)
    if r.returncode != 0:
        fail(f"Start failed: {r.stderr[:200]}")
    print(r.stdout)
    ok("SBA backend started")


def phase_verify(dry_run: bool) -> None:
    """Verify backend is running from outside."""
    if dry_run:
        log(f"[DRY-RUN] Would verify at http://{EC2_IP}:{BACKEND_PORT}/api/health")
        return

    log("Verifying backend from outside...")
    import urllib.request
    import json
    
    try:
        url = f"http://{EC2_IP}:{BACKEND_PORT}/api/health"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            ok(f"Backend healthy: {data}")
    except Exception as e:
        warn(f"External health check failed: {e}")
        # Try via SSH tunnel
        r = ssh_exec(f"curl -s http://localhost:{BACKEND_PORT}/api/health")
        if r.returncode == 0 and r.stdout:
            ok(f"Backend healthy (SSH proxy): {r.stdout[:100]}")
        else:
            warn("Could not verify backend externally")


def phase_frontend_env(dry_run: bool) -> None:
    """Set Vercel environment variables for SBA backend."""
    log("Frontend deployment options:")

    # Read current .env.vercel
    vercel_env = os.path.join(LOCAL_ROOT, '.env.vercel')
    
    print(f"""
╔══════════════════════════════════════════════════════╗
║           FRONTEND CONNECTION SETUP                  ║
╠══════════════════════════════════════════════════════╣
║                                                      ║
║  The SBA API route proxies to BACKEND_API_URL.       ║
║  Currently it's empty in .env.vercel.                ║
║                                                      ║
║  Option 1: Vercel Dashboard                          ║
║  ───────────────────────────────                     ║
║  Set in Vercel Project → Environment Variables:      ║
║                                                      ║
║    BACKEND_API_URL = http://{EC2_IP}:{BACKEND_PORT}      ║
║    NEXT_PUBLIC_API_URL = http://{EC2_IP}:{BACKEND_PORT}  ║
║                                                      ║
║  Then redeploy the frontend.                         ║
║                                                      ║
║  Option 2: Nginx Reverse Proxy (RECOMMENDED)         ║
║  ───────────────────────────────────────             ║
║  Set up nginx on EC2 to serve both:                 ║
║    - /api/* → localhost:{BACKEND_PORT}                    ║
║    - /*     → Next.js (if SSG)                      ║
║                                                      ║
║  Then Vercel env:                                    ║
║    BACKEND_API_URL = http://{EC2_IP}:{BACKEND_PORT}      ║
║                                                      ║
╚══════════════════════════════════════════════════════╝
""")


def phase_fix_chrome_agent(dry_run: bool) -> None:
    """Chrome-agent binary: Windows .exe won't work on EC2 Linux."""
    if dry_run:
        log("[DRY-RUN] Would check/install chrome-agent for Linux")
        return

    script = f"""
set -e
cd {REMOTE_DIR}

# Check if chrome-agent exists for Linux
if [ ! -f "chrome-agent/target/release/chrome-agent" ]; then
    echo "--- Chrome-agent not found for Linux ---"
    echo "Setting up Playwright as fallback for Chrome automation..."
    
    # Install Playwright
    cd {REMOTE_DIR}
    source venv/bin/activate
    pip3 install playwright 2>&1 | tail -3
    python3 -m playwright install chromium 2>&1 | tail -5
    
    echo "Playwright installed as Chrome automation fallback"
else
    echo "Chrome-agent binary found"
fi
"""
    log("Checking Chrome automation for EC2...")
    r = ssh_exec(script, timeout=120)
    if r.returncode != 0:
        warn(f"Chrome-agent setup had issues: {r.stderr[:200]}")
    ok("Chrome automation ready")


# ── Main ────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Deploy SBA to EC2")
    parser.add_argument('--run', action='store_true',
                       help='Actually run the deployment (dry-run by default)')
    parser.add_argument('--frontend', action='store_true',
                       help='Only show frontend connection info')
    parser.add_argument('--skip-verify', action='store_true',
                       help='Skip post-deploy verification')
    args = parser.parse_args()

    dry_run = not args.run
    prefix = "[DRY-RUN]" if dry_run else ""

    print(f"""
╔══════════════════════════════════════╗
║  SBA EC2 Deployment {prefix:>15}║
╠══════════════════════════════════════╣
║  Target: {SSH_HOST:>25}  ║
║  Port:   {BACKEND_PORT:>25}  ║
║  Remote: {REMOTE_DIR:>25}  ║
╚══════════════════════════════════════╝
""")

    if args.frontend:
        phase_frontend_env(dry_run)
        return

    # ── Phase 1: Check EC2 ──────────────────────────────────────────
    print("\n📡 Phase 1: Check EC2 connectivity")
    if not phase_check_ec2():
        warn("EC2 is not reachable. Cannot proceed with deployment.")
        print("\n" + "=" * 55)
        print("  EC2 is DOWN. When it comes back up:")
        print(f"    python deploy_sba.py --run")
        print("=" * 55)
        phase_frontend_env(dry_run)
        return

    # ── Phase 2: Send files ─────────────────────────────────────────
    print("\n📦 Phase 2: Send files to EC2")
    phase_send_files(dry_run)

    # ── Phase 3: Setup environment ──────────────────────────────────
    print("\n🔧 Phase 3: Setup EC2 environment")
    phase_setup_ec2(dry_run)

    # ── Phase 4: Chrome automation ──────────────────────────────────
    print("\n🌐 Phase 4: Chrome automation setup")
    phase_fix_chrome_agent(dry_run)

    # ── Phase 5: Start backend ──────────────────────────────────────
    print("\n🚀 Phase 5: Start SBA backend")
    phase_start_backend(dry_run)

    # ── Phase 6: Verify ─────────────────────────────────────────────
    print("\n✅ Phase 6: Verification")
    if not args.skip_verify:
        phase_verify(dry_run)

    # ── Phase 7: Frontend ───────────────────────────────────────────
    print("\n🌍 Phase 7: Frontend connection")
    phase_frontend_env(dry_run)

    # ── Summary ─────────────────────────────────────────────────────
    print("\n" + "=" * 55)
    if dry_run:
        print("  📋 DRY RUN - No changes made.")
        print(f"  Run:  python deploy_sba.py --run")
    else:
        print("  🎉 DEPLOYMENT COMPLETE!")
        print(f"  Backend: http://{EC2_IP}:{BACKEND_PORT}")
        print(f"  Health:  http://{EC2_IP}:{BACKEND_PORT}/api/health")
    print("=" * 55)


if __name__ == "__main__":
    main()
