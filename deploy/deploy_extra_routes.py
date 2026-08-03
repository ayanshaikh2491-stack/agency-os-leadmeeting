"""Deploy extra.py + workflows.py to EC2 and patch main.py to include them."""
import subprocess, time, sys

KEY = r'C:\Users\TAUSHEF\Downloads\int\ec2-key.pem'
HOST = 'ubuntu@18.213.66.136'
REMOTE = '/home/ubuntu/sba-backend'
FILES = [
    (r'C:\Users\TAUSHEF\Downloads\int\admin\api\routes\extra.py', 'admin/api/routes/extra.py'),
    (r'C:\Users\TAUSHEF\Downloads\int\admin\api\routes\workflows.py', 'admin/api/routes/workflows.py'),
]


def ssh(cmd, timeout=40, attempts=8, retry_delay=2.0):
    last = None
    for i in range(attempts):
        try:
            r = subprocess.run(
                ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
                 "-o", "ConnectTimeout=15", "-i", KEY, HOST, cmd],
                capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace",
            )
            return r
        except subprocess.TimeoutExpired:
            last = 'TIMEOUT'
        except Exception as e:
            last = f'ERR {e}'
        time.sleep(retry_delay)
    r = subprocess.CompletedProcess([], 1)
    r.stderr = str(last)
    return r


def scp(local, remote_path, timeout=60):
    last = None
    for i in range(8):
        try:
            r = subprocess.run(
                ["scp", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
                 "-o", "ConnectTimeout=15", "-i", KEY, local, f"{HOST}:{remote_path}"],
                capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace",
            )
            return r
        except subprocess.TimeoutExpired:
            last = 'TIMEOUT'
        except Exception as e:
            last = f'ERR {e}'
        time.sleep(retry_delay := 2.0)
    r = subprocess.CompletedProcess([], 1)
    r.stderr = str(last)
    return r


def log(*a):
    print(*a, flush=True)


def main() -> int:
    # 1. upload files
    for local, remote_rel in FILES:
        r = scp(local, f"{REMOTE}/{remote_rel}")
        log(f"scp {remote_rel}:", (r.stdout or r.stderr or '').strip()[-200:] or 'OK')
        if r.returncode != 0:
            return 1

    # 2. patch main.py to include extra + workflows routers
    patch = (
        "cd %s && python3 - <<'PY'\n"
        "p = 'admin/main.py'\n"
        "s = open(p, encoding='utf-8').read()\n"
        "if 'extra_routes' not in s:\n"
        "    s = s.replace('from admin.api.routes import compat as compat_routes',\n"
        "                  'from admin.api.routes import compat as compat_routes\\n"
        "from admin.api.routes import extra as extra_routes\\n"
        "from admin.api.routes import workflows as workflows_routes')\n"
        "    s = s.replace('app.include_router(compat_routes.router)',\n"
        "                  'app.include_router(compat_routes.router)\\n"
        "app.include_router(extra_routes.router)\\n"
        "app.include_router(workflows_routes.router)')\n"
        "    open(p, 'w', encoding='utf-8').write(s)\n"
        "    print('PATCHED')\n"
        "else:\n"
        "    print('ALREADY')\n"
        "PY" % REMOTE
    )
    r = ssh(patch)
    out = (r.stdout or r.stderr or '').strip()
    log("main.py patch:", out[-300:])
    if 'PATCHED' not in out and 'ALREADY' not in out:
        return 2

    # 3. py_compile
    r = ssh(f"cd {REMOTE} && venv/bin/python -m py_compile admin/api/routes/extra.py admin/api/routes/workflows.py admin/main.py && echo COMPILE_OK", timeout=90)
    log("py_compile:", (r.stdout or r.stderr or '').strip()[-200:] or '(empty)')
    if 'COMPILE_OK' not in (r.stdout or ''):
        return 3

    # 4. restart backend
    r = ssh("sudo systemctl restart sba.service && sleep 8 && systemctl is-active sba.service", timeout=120)
    log("sba.service:", (r.stdout or r.stderr or '').strip()[-200:])
    if 'active' not in (r.stdout or ''):
        j = ssh("journalctl -u sba.service -n 30 --no-pager | tail -20", timeout=30)
        log((j.stdout or j.stderr or '').strip()[-1200:])
        return 4

    # 5. verify live
    for path in ['/api/status', '/api/workflows', '/api/social/tokens/status']:
        r = ssh(f"curl -s -m 20 -o /dev/null -w '%{{http_code}}' http://127.0.0.1:8000{path}", timeout=40)
        log(f"{path}:", (r.stdout or r.stderr or '').strip() or '(no code)')

    log("DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
