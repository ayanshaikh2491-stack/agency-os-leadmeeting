"""Deploy SBA 24/7 feature branch to the EC2 server.

Usage:  python deploy/deploy_sba.py
Safe:   checks connectivity first (fast TCP pre-check), uploads files,
        py_compile on server, restarts sba.service, verifies it is active.

Server: ubuntu@18.213.66.136  (key: ec2-key.pem in repo root)
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys

KEY = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"
HOST_IP = HOST.split("@")[-1]
REMOTE_ROOT = "/home/ubuntu/sba-backend"
CONNECT_TIMEOUT = 10
SSH_TIMEOUT = 25

# Files changed on this branch (git diff --name-status d0005f1 HEAD)
FILES = [
    "admin/agency/sba_autopilot.py",
    "admin/agency/sba_pipeline.py",
    "admin/api/routes/sba.py",
    "admin/config/settings.py",
    "admin/tests/test_autopilot_integration.py",
    "admin/tests/test_sba_autopilot.py",
    "admin/tests/test_sba_email_draft.py",
    "admin/tests/test_sba_lead_sources.py",
    "admin/tests/test_sba_pipeline_helpers.py",
    "admin/tests/test_sba_time.py",
    "admin/tests/test_sba_translate_notes.py",
    "admin/tools/chrome_tool.py",
    "admin/tools/sba_email_draft.py",
    "admin/tools/sba_lead_sources.py",
    "admin/tools/sba_time.py",
    "admin/tools/sba_translate.py",
    "deploy/sba-autopilot.service",
    "docs/sba_autopilot_deploy.md",
]


class _Failed:
    returncode = 1
    stdout = ""
    stderr = ""


def ssh(cmd: str, timeout: int = SSH_TIMEOUT, attempts: int = 4) -> subprocess.CompletedProcess:
    import time as _time
    last: subprocess.CompletedProcess | None = None
    for _ in range(attempts):
        try:
            r = subprocess.run(
                ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
                 "-o", f"ConnectTimeout={CONNECT_TIMEOUT}",
                 "-i", KEY, HOST, cmd],
                capture_output=True, text=True, timeout=timeout,
                encoding="utf-8", errors="replace",
            )
            if r.returncode == 0 or (r.stdout or r.stderr):
                return r
            last = r
        except subprocess.TimeoutExpired:
            last = None
        _time.sleep(1.5)
    if last is not None:
        return last
    f = _Failed()
    f.stderr = "SSH timed out after retries"
    return f  # type: ignore[return-value]


def scp(local: str, remote: str, timeout: int = 120) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            ["scp", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
             "-o", f"ConnectTimeout={CONNECT_TIMEOUT}",
             "-i", KEY, local, f"{HOST}:{remote}"],
            capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace",
        )
    except subprocess.TimeoutExpired:
        f = _Failed()
        f.stderr = "SCP timed out"
        return f  # type: ignore[return-value]


def main() -> int:
    if not os.path.exists(KEY):
        print(f"FATAL: key not found: {KEY}")
        return 1

    # 0. Fast TCP pre-check (port 22) - fail fast instead of hanging SSH
    try:
        sock = socket.create_connection((HOST_IP, 22), timeout=6)
        sock.close()
        print(f"TCP {HOST_IP}:22 open.")
    except Exception as exc:
        print(f"Server unreachable (TCP {HOST_IP}:22): {exc}")
        print("Deploy aborted. EC2 instance chalu karo / security group check karo, phir dobara chalao.")
        return 2

    # 1. SSH connectivity
    r = ssh("echo CONN_OK", timeout=30)
    if r.returncode != 0 or "CONN_OK" not in (r.stdout or ""):
        print("SSH handshake failed - deploy aborted.")
        print((r.stderr or r.stdout or "").strip()[-500:])
        return 2

    print("Server reachable.")

    # 2. Upload files
    for f in FILES:
        remote = f"{REMOTE_ROOT}/{f}"
        parent = remote.rsplit("/", 1)[0]
        ssh(f"mkdir -p {parent}", timeout=20)
        r = scp(f, remote)
        if r.returncode != 0:
            print(f"  upload FAILED: {f}\n  {(r.stderr or '').strip()[-300:]}")
            return 3
        print(f"  uploaded {f}")

    # 3. Compile check on server
    r = ssh(
        "cd %s && sudo python3 -m py_compile admin/agency/sba_autopilot.py "
        "admin/agency/sba_pipeline.py admin/api/routes/sba.py admin/config/settings.py "
        "admin/tools/chrome_tool.py admin/tools/sba_email_draft.py admin/tools/sba_lead_sources.py "
        "admin/tools/sba_time.py admin/tools/sba_translate.py && echo COMPILE_OK"
        % REMOTE_ROOT,
        timeout=60,
    )
    if "COMPILE_OK" not in (r.stdout or ""):
        print("Server py_compile FAILED.")
        print((r.stdout or r.stderr or "").strip()[-800:])
        return 4
    print("Server py_compile OK.")

    # 4. Install systemd unit (if it changed)
    ssh("sudo cp %s/deploy/sba-autopilot.service /etc/systemd/system/ && "
        "sudo systemctl daemon-reload" % REMOTE_ROOT, timeout=30)

    # 5. Restart service
    r = ssh("sudo systemctl restart sba.service && sleep 6 && systemctl is-active sba.service",
            timeout=60)
    active = (r.stdout or "").strip()
    print("sba.service:", active or (r.stderr or "").strip()[-300:])
    if active != "active":
        j = ssh("journalctl -u sba.service -n 30 --no-pager | tail -20", timeout=30)
        print((j.stdout or j.stderr or "").strip()[-1200:])
        return 5

    # 6. Verify translate-page route present
    r = ssh(
        "cd %s && sudo python3 -c \"import admin.api.routes.sba as m; "
        "print(any('translate-page' in getattr(r,'path','') for r in m.router.routes))\""
        % REMOTE_ROOT,
        timeout=60,
    )
    print("translate-page route present:", (r.stdout or "").strip())

    print("\nDEPLOY OK - SBA 24/7 feature branch live.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
