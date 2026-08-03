"""Deploy updated extra.py to EC2 and restart sba.service."""
import subprocess, time, sys

KEY = r'C:\Users\TAUSHEF\Downloads\int\ec2-key.pem'
HOST = 'ubuntu@18.213.66.136'
REMOTE = '/home/ubuntu/sba-backend'


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


def log(*a):
    print(*a, flush=True)


def main() -> int:
    local = r'C:\Users\TAUSHEF\Downloads\int\admin\api\routes\extra.py'
    r = subprocess.run(
        ["scp", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
         "-o", "ConnectTimeout=15", "-i", KEY, local, f"{HOST}:{REMOTE}/admin/api/routes/extra.py"],
        capture_output=True, text=True, timeout=60, encoding="utf-8", errors="replace",
    )
    log("scp extra.py:", (r.stdout or r.stderr or '').strip()[-200:] or 'OK')
    if r.returncode != 0:
        return 1

    r = ssh(f"cd {REMOTE} && venv/bin/python -m py_compile admin/api/routes/extra.py && echo COMPILE_OK", timeout=90)
    log("py_compile:", (r.stdout or r.stderr or '').strip()[-200:] or '(empty)')
    if 'COMPILE_OK' not in (r.stdout or ''):
        return 2

    r = ssh("sudo systemctl restart sba.service && sleep 8 && systemctl is-active sba.service", timeout=120)
    log("sba.service:", (r.stdout or r.stderr or '').strip()[-200:])
    if 'active' not in (r.stdout or ''):
        j = ssh("journalctl -u sba.service -n 30 --no-pager | tail -20", timeout=30)
        log((j.stdout or j.stderr or '').strip()[-1200:])
        return 3

    for path in ['/api/status', '/api/workspaces', '/api/agents/seo-engine/status', '/api/agents/website-builder/status']:
        r = ssh(f"curl -s -m 20 -o /dev/null -w '%{{http_code}}' http://127.0.0.1:8000{path}", timeout=40)
        log(f"{path}:", (r.stdout or r.stderr or '').strip() or '(no code)')

    log("DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
