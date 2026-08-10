"""Remote: check backfill death - log tail + any traceback."""
import subprocess, sys, os, time
sys.path.insert(0, os.getcwd())
KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=40, tries=3):
    last = None
    for i in range(tries):
        try:
            r = subprocess.run(
                ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
                 "-o", "ConnectTimeout=15", "-i", KEY, HOST, cmd],
                capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
            if r.returncode == 0 or r.stdout.strip():
                return r
            last = r
        except Exception as e:
            last = e
        time.sleep(3)
    return last

def show(title, cmd):
    print(f"\n=== {title} ===")
    r = ssh(cmd)
    if isinstance(r, subprocess.CompletedProcess):
        print(r.stdout.strip() or "(empty rc=%s)" % r.returncode)
        if r.stderr.strip(): print("ERR:", r.stderr[:400])
    else:
        print("FAILED:", r)

show("backfill log tail", "tail -30 /home/ubuntu/sba-backend/_backfill.log")
show("backfill log size", "wc -l /home/ubuntu/sba-backend/_backfill.log; ls -la /home/ubuntu/sba-backend/_backfill.log")
show("all python procs", "ps aux | grep -E 'python.*(backfill|enrich)' | grep -v grep | head -5; echo '---'; ps aux | grep python3 | grep -v grep | wc -l")
show("chrome procs count", "pgrep -c -f remote-debugging-port=9252 || echo 0")
