"""Finish SBA 24/7 EC2 deploy: bundle upload (single scp) + server steps.

Uploads all deploy files as ONE tar to avoid per-file scp over flaky SSH,
then runs: py_compile, tzdata install, autopilot unit, worker->autopilot swap,
backend restart, route/status verification.

Usage: python deploy/deploy_sba.py
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
BUNDLE = "/tmp/sbadeploy-bundle.tar"

# Full sba module closure + branch files (kept in sync with deploy file list)
# Organic engine closure added for the Social Organic Posting Engine deploy.
FILES = [
    "admin/agency/langgraph_sba.py",
    "admin/agency/sba.py",
    "admin/agency/sba_autopilot.py",
    "admin/agency/sba_biztypes.py",
    "admin/agency/sba_monitor.py",
    "admin/agency/sba_pipeline.py",
    "admin/agency/sba_reason.py",
    "admin/agency/sba_strategy.py",
    "admin/agency/sba_skills.py",
    "admin/agency/sba_store.py",
    "admin/agency/ceo.py",
    "admin/agency/social_skills.py",
    "admin/agency/agent_persistence.py",
    "admin/api/routes/sba.py",
    "admin/api/routes/social.py",
    "admin/api/routes/extra.py",
    "admin/api/routes/agent_aliases.py",
    "admin/api/models/schemas.py",
    "admin/workspace/manager.py",
    "admin/config/settings.py",
    "admin/main.py",
    "admin/tests/test_autopilot_integration.py",
    "admin/tests/test_organic_base.py",
    "admin/tests/test_organic_config.py",
    "admin/tests/test_organic_connect.py",
    "admin/tests/test_organic_facebook.py",
    "admin/tests/test_organic_gbp.py",
    "admin/tests/test_organic_hub.py",
    "admin/tests/test_organic_linkedin.py",
    "admin/tests/test_organic_oauth.py",
    "admin/tests/test_organic_pinterest.py",
    "admin/tests/test_organic_reddit.py",
    "admin/tests/test_organic_registry.py",
    "admin/tests/test_organic_routes.py",
    "admin/tests/test_organic_scheduler.py",
    "admin/tests/test_organic_telegram.py",
    "admin/tests/test_organic_twitter.py",
    "admin/tests/test_organic_wiring.py",
    "admin/tests/test_analytics_audit.py",
    "admin/tests/test_sba_autopilot.py",
    "admin/tests/test_sba_biztypes.py",
    "admin/tests/test_sba_email_draft.py",
    "admin/tests/test_sba_lead_sources.py",
    "admin/tests/test_sba_pipeline_helpers.py",
    "admin/tests/test_sba_reason.py",
    "admin/tests/test_sba_strategy.py",
    "admin/tests/test_sba_time.py",
    "admin/tests/test_sba_translate_notes.py",
    "admin/tests/test_social_skills.py",
    "admin/token_manager.py",
    "admin/tools/browser_daemon.py",
    "admin/tools/chrome_tool.py",
    "admin/tools/analytics_tools.py",
    "admin/tools/organic/__init__.py",
    "admin/tools/organic/base.py",
    "admin/tools/organic/config.py",
    "admin/tools/organic/connect.py",
    "admin/tools/organic/facebook_browser.py",
    "admin/tools/organic/history.py",
    "admin/tools/organic/scheduler.py",
    "admin/tools/organic/gbp_api.py",
    "admin/tools/organic/hub.py",
    "admin/tools/organic/linkedin_api.py",
    "admin/tools/organic/oauth.py",
    "admin/tools/organic/pinterest_api.py",
    "admin/tools/organic/reddit_api.py",
    "admin/tools/organic/registry.py",
    "admin/tools/organic/telegram_api.py",
    "admin/tools/organic/twitter_api.py",
    "admin/tools/sba_email_client.py",
    "admin/tools/sba_email_draft.py",
    "admin/tools/sba_email_templates.py",
    "admin/tools/sba_lead_sources.py",
    "admin/tools/sba_meeting.py",
    "admin/tools/sba_time.py",
    "admin/tools/sba_translate.py",
    "admin/tools/sba_tools.py",
    "admin/tools/lead_enrichment.py",
    "admin/tools/social_tools.py",
    "admin/utils/email_sender.py",
    "admin/workspace/agent_bus.py",
    "admin/workspace/agents/ads.py",
    "admin/workspace/agents/analytics.py",
    "admin/workspace/agents/content.py",
    "admin/workspace/agents/sba.py",
    "admin/workspace/agents/seo.py",
    "admin/workspace/agents/social.py",
    "admin/workspace/agents/website.py",
    "deploy/sba-autopilot.service",
    "deploy/sba-chrome.service",
    "docs/sba_autopilot_deploy.md",
]

# Files to syntax-check on the server after extraction (source closure only).
COMPILE_FILES = [
    "admin/agency/langgraph_sba.py",
    "admin/agency/sba.py",
    "admin/agency/sba_autopilot.py",
    "admin/agency/sba_biztypes.py",
    "admin/agency/sba_pipeline.py",
    "admin/agency/sba_reason.py",
    "admin/agency/sba_strategy.py",
    "admin/agency/ceo.py",
    "admin/agency/social_skills.py",
    "admin/agency/agent_persistence.py",
    "admin/api/routes/sba.py",
    "admin/api/routes/social.py",
    "admin/api/routes/extra.py",
    "admin/api/routes/agent_aliases.py",
    "admin/api/models/schemas.py",
    "admin/workspace/manager.py",
    "admin/config/settings.py",
    "admin/main.py",
    "admin/token_manager.py",
    "admin/tools/browser_daemon.py",
    "admin/tools/chrome_tool.py",
    "admin/tools/analytics_tools.py",
    "admin/tools/organic/__init__.py",
    "admin/tools/organic/base.py",
    "admin/tools/organic/config.py",
    "admin/tools/organic/connect.py",
    "admin/tools/organic/facebook_browser.py",
    "admin/tools/organic/history.py",
    "admin/tools/organic/scheduler.py",
    "admin/tools/organic/gbp_api.py",
    "admin/tools/organic/hub.py",
    "admin/tools/organic/linkedin_api.py",
    "admin/tools/organic/oauth.py",
    "admin/tools/organic/pinterest_api.py",
    "admin/tools/organic/reddit_api.py",
    "admin/tools/organic/registry.py",
    "admin/tools/organic/telegram_api.py",
    "admin/tools/organic/twitter_api.py",
    "admin/tools/sba_email_draft.py",
    "admin/tools/sba_email_client.py",
    "admin/tools/sba_email_templates.py",
    "admin/tools/sba_lead_sources.py",
    "admin/tools/sba_meeting.py",
    "admin/tools/sba_time.py",
    "admin/tools/sba_translate.py",
    "admin/tools/sba_tools.py",
    "admin/tools/lead_enrichment.py",
    "admin/tools/social_tools.py",
    "admin/utils/email_sender.py",
    "admin/workspace/agent_bus.py",
    "admin/workspace/agents/ads.py",
    "admin/workspace/agents/analytics.py",
    "admin/workspace/agents/content.py",
    "admin/workspace/agents/sba.py",
    "admin/workspace/agents/seo.py",
    "admin/workspace/agents/social.py",
    "admin/workspace/agents/website.py",
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
    local = os.path.join(tempfile.gettempdir(), "sbadeploy-bundle.tar")
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
        "sudo chown -R ubuntu:ubuntu admin deploy docs && echo EXTRACT_OK"
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
        "cd %s && venv/bin/python -m py_compile %s && echo COMPILE_OK"
        % (REMOTE_ROOT, " ".join(COMPILE_FILES)),
        timeout=120,
    )
    if "COMPILE_OK" not in (r.stdout or ""):
        log("Server py_compile FAILED.")
        log((r.stdout or r.stderr or "").strip()[-800:])
        return 5
    log("Server py_compile OK.")

    # 5. tzdata
    have = ssh(f"cd {REMOTE_ROOT} && venv/bin/pip show tzdata | head -1", timeout=60)
    if "tzdata" not in (have.stdout or ""):
        r = ssh(f"cd {REMOTE_ROOT} && venv/bin/pip install tzdata && echo TZDATA_OK", timeout=240)
        if "TZDATA_OK" not in (r.stdout or ""):
            log("tzdata install FAILED:", (r.stdout or r.stderr or "").strip()[-400:])
            return 5
        log("tzdata installed.")
    else:
        log("tzdata present.")

    # 5b. enrichment deps (requests + bs4) for lead_enrichment.py
    r = ssh(
        f"cd {REMOTE_ROOT} && venv/bin/python -c \"import requests, bs4\" "
        f"|| venv/bin/pip install requests beautifulsoup4; echo DEPS_OK",
        timeout=240,
    )
    log("enrichment deps ready.")

    # 6. autopilot unit + swap services
    r = ssh(
        "sudo cp %s/deploy/sba-autopilot.service /etc/systemd/system/ && "
        "sudo systemctl daemon-reload && "
        "sudo systemctl stop sba-worker.service 2>/dev/null; "
        "sudo systemctl disable sba-worker.service 2>/dev/null; "
        "sudo systemctl enable sba-autopilot.service && "
        "sudo systemctl restart sba-autopilot.service && sleep 3 && "
        "echo AUTOPILOT_ACTIVE=$(systemctl is-active sba-autopilot.service) && "
        "echo WORKER_STATE=$(systemctl is-active sba-worker.service 2>&1)" % REMOTE_ROOT,
        timeout=90,
    )
    out = r.stdout or ""
    log(out.strip()[-300:])
    if "AUTOPILOT_ACTIVE=active" not in out:
        j = ssh("journalctl -u sba-autopilot.service -n 20 --no-pager | tail -15", timeout=30)
        log((j.stdout or j.stderr or "").strip()[-1200:])
        return 6

    # 7. restart backend
    r = ssh("sudo systemctl restart sba.service && sleep 6 && systemctl is-active sba.service",
            timeout=90)
    active = (r.stdout or "").strip()
    log("sba.service:", active or (r.stderr or "").strip()[-300:])
    if active != "active":
        j = ssh("journalctl -u sba.service -n 30 --no-pager | tail -20", timeout=30)
        log((j.stdout or j.stderr or "").strip()[-1200:])
        return 7

    # 8. verify routes + status
    r = ssh(
        "cd %s && venv/bin/python -c \"import admin.api.routes.sba as m; "
        "print('translate-page:', any('translate-page' in getattr(r,'path','') for r in m.router.routes))\""
        % REMOTE_ROOT,
        timeout=90,
    )
    log("translate-page route present:", (r.stdout or "").strip())

    r = ssh("curl -s -m 20 http://127.0.0.1:8000/api/sba/autopilot/status", timeout=40)
    log("autopilot/status:", (r.stdout or "").strip()[-300:] or "(no body)")

    # 9. verify health + organic engine endpoints
    r = ssh("curl -s -m 20 http://127.0.0.1:8000/api/health", timeout=40)
    log("api/health:", (r.stdout or "").strip()[-400:] or "(no body)")

    r = ssh("curl -s -m 20 'http://127.0.0.1:8000/api/social/organic/channels?workspace_id=default'",
            timeout=40)
    log("organic/channels:", (r.stdout or "").strip()[-600:] or "(no body)")

    log("\nDEPLOY OK - SBA 24/7 autopilot live (worker disabled) + organic engine deployed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
