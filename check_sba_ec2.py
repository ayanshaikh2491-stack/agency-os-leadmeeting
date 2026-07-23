"""Check SBA backend status on EC2."""
import subprocess
r = subprocess.run(
    ['ssh', '-i', 'ec2-key.pem', '-o', 'ConnectTimeout=5',
     '-o', 'StrictHostKeyChecking=no', 'ubuntu@18.213.66.136',
     'ps aux | grep admin.main | grep -v grep; echo "---"; curl -s --max-time 3 http://localhost:9002/api/health || echo "DOWN"; echo "---"; tail -5 /tmp/sba.log 2>/dev/null || echo "no log"'],
    capture_output=True, text=True, timeout=15
)
print(r.stdout[:500])
if r.stderr.strip(): print(r.stderr[:200])
