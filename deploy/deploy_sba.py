"""Deploy SBA 24/7 feature branch to the EC2 server.

Usage:  python deploy/deploy_sba.py
Safe:   checks connectivity first (fast TCP pre-check), uploads files,
        py_compile on server, installs tzdata, restarts sba.service,
        swaps worker -> autopilot services, verifies routes/status API.

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
SSH_TIMEOUT = 30

# Files changed on this branch (git diff --name-status d0005f1 HEAD) PLUS the
# full sba module closure so imports resolve on a fresh server (sba_meeting,
# sba_email_client/templates, agency/sba*, langgraph_sba are imported by the
# deployed modules and were missing in earlier runs).
FILES = [
    "admin/agency/langgraph_sba.py",
    "admin/agency/sba.py",
    "admin/agency/sba_autopilot.py",
    "admin/agency/sba_monitor.py",
    "admin/agency/sba_pipeline.py",
    "admin/agency/sba_skills.py",
    "admin/agency/sba_store.py",
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
    "admin/tools/sba_email_client.py",
    "admin/tools/sba_email_draft.py",
    "admin/tools/sba_email_templates.py",
    "admin/tools/sba_lead_sources.py",
    "admin/tools/sba_meeting.py",
    "admin/tools/sba_time.py",
    "admin/tools/sba_translate.py",
    "deploy/sba-autopilot.service",
    "docs/sba_autopilot_deploy.md",
]


class _Failed:
    returncode = 1
    stdout = ""
    stderr = ""


def log(*a):
    print(*a, flush=True)


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


def run(cmd: str, timeout: int = SSH_TIMEOUT, attempts: int = 4) -> str:
    """Run remote command, retry on empty result, return stdout or ''."""
    r = ssh(cmd, timeout=timeout, attempts=attempts)
    return (r.stdout or "").strip()


def main() -> int:
    if not os.path.exists(KEY):
        log(f"FATAL: key not found: {KEY}")
        return 1

    # 0. Fast TCP pre-check (port 22) - fail fast instead of hanging SSH
    try:
        sock = socket.create_connection((HOST_IP, 22), timeout=6)
        sock.close()
        log(f"TCP {HOST_IP}:22 open.")
    except Exception as exc:
        log(f"Server unreachable (TCP {HOST_IP}:22): {exc}")
        log("Deploy aborted. EC2 instance chalu karo / security group check karo, phir dobara chalao.")
        return 2

    # 1. SSH connectivity
    r = ssh("echo CONN_OK", timeout=30)
    if r.returncode != 0 or "CONN_OK" not in (r.stdout or ""):
        log("SSH handshake failed - deploy aborted.")
        log((r.stderr or r.stdout or "").strip()[-500:])
        return 2

    log("Server reachable.")

    # 2. Upload files
    for f in FILES:
        remote = f"{REMOTE_ROOT}/{f}"
        parent = remote.rsplit("/", 1)[0]
        ssh(f"mkdir -p {parent}", timeout=20)
        r = scp(f, remote)
        if r.returncode != 0:
            log(f"  upload FAILED: {f}\n  {(r.stderr or '').strip()[-300:]}")
            return 3
        log(f"  uploaded {f}")

    # 3. Compile check on server (venv python - syntax only, no fastapi import needed)
    r = ssh(
        "cd %s && venv/bin/python -m py_compile "
        "admin/agency/sba_autopilot.py admin/agency/sba_pipeline.py "
        "admin/agency/sba.py admin/agency/langgraph_sba.py "
        "admin/api/routes/sba.py admin/config/settings.py "
        "admin/tools/chrome_tool.py admin/tools/sba_email_draft.py "
        "admin/tools/sba_email_client.py admin/tools/sba_email_templates.py "
        "admin/tools/sba_lead_sources.py admin/tools/sba_meeting.py "
        "admin/tools/sba_time.py admin/tools/sba_translate.py && echo COMPILE_OK"
        % REMOTE_ROOT,
        timeout=90,
    )
    if "COMPILE_OK" not in (r.stdout or ""):
        log("Server py_compile FAILED.")
        log((r.stdout or r.stderr or "").strip()[-800:])
        return 4
    log("Server py_compile OK.")

    # 4. Install tzdata if missing (idempotent)
    have_tz = run(f"cd {REMOTE_ROOT} && venv/bin/pip show tzdata | head -1", timeout=60)
    if "tzdata" not in have_tz:
        r = ssh(f"cd {REMOTE_ROOT} && venv/bin/pip install tzdata && echo TZDATA_OK", timeout=180)
        if "TZDATA_OK" not in (r.stdout or ""):
            log("tzdata install FAILED.")
            log((r.stdout or r.stderr or "").strip()[-500:])
            return 4
        log("tzdata installed.")
    else:
        log("tzdata already present.")

    # 5. Install autopilot systemd unit + reload
    ssh("sudo cp %s/deploy/sba-autopilot.service /etc/systemd/system/ && "
        "sudo systemctl daemon-reload" % REMOTE_ROOT, timeout=30)
    log("autopilot unit installed.")

    # 6. Swap services: stop+disable old worker, enable+start autopilot
    r = ssh("sudo systemctl stop sba-worker.service 2>/dev/null; "
            "sudo systemctl disable sba-worker.service 2>/dev/null; "
            "sudo systemctl enable sba-autopilot.service && "
            "sudo systemctl restart sba-autopilot.service && sleep 3 && "
            "echo AUTOPILOT_ACTIVE=$(systemctl is-active sba-autopilot.service)", timeout=60)
    out = r.stdout or ""
    log("autopilot service:", out.strip()[-200:])
    if "AUTOPILOT_ACTIVE=active" not in out:
        j = ssh("journalctl -u sba-autopilot.service -n 20 --no-pager | tail -15", timeout=30)
        log((j.stdout or j.stderr or "").strip()[-1200:])
        return 5

    # 7. Restart backend service
    r = ssh("sudo systemctl restart sba.service && sleep 6 && systemctl is-active sba.service",
            timeout=60)
    active = (r.stdout or "").strip()
    log("sba.service:", active or (r.stderr or "").strip()[-300:])
    if active != "active":
        j = ssh("journalctl -u sba.service -n 30 --no-pager | tail -20", timeout=30)
        log((j.stdout or j.stderr or "").strip()[-1200:])
        return 6

    # 8. Verify routes + status API (venv python for fastapi import)
    r = ssh(
        "cd %s && venv/bin/python -c \"import admin.api.routes.sba as m; "
        "print('translate-page:', any('translate-page' in getattr(r,'path','') for r in m.router.routes))\""
        % REMOTE_ROOT,
        timeout=60,
    )
    log("translate-page route present:", (r.stdout or "").strip())

    r = ssh("curl -s -m 20 http://127.0.0.1:8000/api/sba/autopilot/status", timeout=40)
    log("autopilot/status:", (r.stdout or "").strip()[-300:] or "(no body)")

    log("\nDEPLOY OK - SBA 24/7 autopilot live (worker disabled).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
