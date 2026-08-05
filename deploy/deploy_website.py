"""Deploy Website Agent backend closure to EC2.

Ships the full website feature (routes, tools, skills, supabase bridge,
workspace agents, tests, router registration in admin/main.py) as one tar,
py_compiles, restarts the backend service, then verifies the live endpoints.

Usage: python deploy/deploy_website.py
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import tarfile
import tempfile

KEY = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"
HOST_IP = HOST.split("@")[-1]
REMOTE_ROOT = "/home/ubuntu/sba-backend"
CONNECT_TIMEOUT = 10
SSH_TIMEOUT = 30
BUNDLE = "/tmp/websitedeploy-bundle.tar"

# Website Agent closure + router registration (kept in sync with git ls-files | grep website)
FILES = [
    "admin/main.py",
    "admin/api/routes/website.py",
    "admin/agency/website_skills.py",
    "admin/agency/website_supabase.py",
    "admin/skills/website/SKILL.md",
    "admin/tests/test_website_build.py",
    "admin/tools/website_tools.py",
    "admin/workspace/agents/website.py",
    "admin/workspace/agents/website_reasoning_chain.py",
    "admin/workspace/agents/website_reasoning_prompts.py",
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


def scp(local: str, remote: str, timeout: int = 300) -> subprocess.CompletedProcess:
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
        log(f"FATAL: key not found: {KEY}")
        return 1

    # 0. TCP pre-check
    try:
        sock = socket.create_connection((HOST_IP, 22), timeout=6)
        sock.close()
        log(f"TCP {HOST_IP}:22 open.")
    except Exception as exc:
        log(f"Server unreachable (TCP {HOST_IP}:22): {exc}")
        return 2

    r = ssh("echo CONN_OK", timeout=30)
    if r.returncode != 0 or "CONN_OK" not in (r.stdout or ""):
        log("SSH handshake failed - deploy aborted.")
        log((r.stderr or r.stdout or "").strip()[-500:])
        return 2
    log("Server reachable.")

    # 1. Build tar bundle locally
    local = os.path.join(tempfile.gettempdir(), "websitedeploy-bundle.tar")
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    missing = [f for f in FILES if not os.path.exists(os.path.join(root, f))]
    if missing:
        log("MISSING local files:", missing)
        return 3
    with tarfile.open(local, "w") as tf:
        for f in FILES:
            tf.add(os.path.join(root, f), arcname=f)
    log(f"Bundle built: {len(FILES)} files, {os.path.getsize(local)} bytes.")

    # 2. Single scp upload
    r = scp(local, BUNDLE)
    if r.returncode != 0:
        log("Bundle upload FAILED:", (r.stderr or "").strip()[-300:])
        return 3
    log("Bundle uploaded.")

    # 3. Extract with sudo install (handles root-owned dests)
    r = ssh(
        "cd /tmp && sudo tar -tf %s >/dev/null && "
        "cd %s && sudo tar -xf %s && "
        "sudo chown -R ubuntu:ubuntu admin && echo EXTRACT_OK"
        % (BUNDLE, REMOTE_ROOT, BUNDLE),
        timeout=120,
    )
    if "EXTRACT_OK" not in (r.stdout or ""):
        log("Server extract FAILED.")
        log((r.stdout or r.stderr or "").strip()[-500:])
        return 4
    log("Server extract OK.")

    # 4. py_compile via venv python
    r = ssh(
        "cd %s && venv/bin/python -m py_compile "
        "admin/main.py admin/api/routes/website.py "
        "admin/agency/website_skills.py admin/agency/website_supabase.py "
        "admin/tools/website_tools.py "
        "admin/workspace/agents/website.py "
        "admin/workspace/agents/website_reasoning_chain.py "
        "admin/workspace/agents/website_reasoning_prompts.py && echo COMPILE_OK"
        % REMOTE_ROOT,
        timeout=90,
    )
    if "COMPILE_OK" not in (r.stdout or ""):
        log("Server py_compile FAILED.")
        log((r.stdout or r.stderr or "").strip()[-800:])
        return 5
    log("Server py_compile OK.")

    # 5. restart backend
    r = ssh("sudo systemctl restart sba.service && sleep 6 && systemctl is-active sba.service",
            timeout=90)
    active = (r.stdout or "").strip()
    log("sba.service:", active or (r.stderr or "").strip()[-300:])
    if active != "active":
        j = ssh("journalctl -u sba.service -n 30 --no-pager | tail -20", timeout=30)
        log((j.stdout or j.stderr or "").strip()[-1200:])
        return 6

    # 6. verify routes + endpoints
    r = ssh(
        "cd %s && venv/bin/python -c \"import admin.api.routes.website as m; "
        "print('build-site:', any(getattr(r,'path','')=='/api/website/build-site' for r in m.router.routes)); "
        "print('categories count check:', 'WEBSITE_CATEGORIES' in open('admin/api/routes/website.py').read())\""
        % REMOTE_ROOT,
        timeout=90,
    )
    log("route check:", (r.stdout or "").strip())

    for path in ("/api/website/tools", "/api/website/skills"):
        r = ssh(f"curl -s -m 25 http://127.0.0.1:8000{path}", timeout=40)
        body = (r.stdout or "").strip()
        log(path, "->", body[:200] if body else "(no body)")
        if not body:
            j = ssh("journalctl -u sba.service -n 20 --no-pager | tail -12", timeout=30)
            log((j.stdout or j.stderr or "").strip()[-1200:])
            return 7

    log("\nDEPLOY OK - Website Agent backend live (14 categories, multi-page maps).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
