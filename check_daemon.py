import subprocess
key = 'ec2-key.pem'
host = 'ubuntu@18.213.66.136'

# Simple checks
cmds = [
    ('systemctl', 'sudo systemctl is-active sba-chrome'),
    ('cdp_test', 'curl -s --max-time 5 http://localhost:9222/json/version'),
    ('port', 'sudo ss -tlnp | grep 9222'),
]
for name, cmd in cmds:
    try:
        r = subprocess.run(['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=5', host, cmd],
            capture_output=True, text=True, timeout=10)
        print(f"{name}: {r.stdout[:200]}")
        if r.stderr.strip(): print(f"  err: {r.stderr[:100]}")
    except Exception as e:
        print(f"{name}: FAILED - {e}")
