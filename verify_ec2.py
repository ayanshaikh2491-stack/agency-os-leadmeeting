"""Verify EC2 SBA after fix."""
import subprocess
r = subprocess.run(
    ['ssh', '-i', 'ec2-key.pem', '-o', 'StrictHostKeyChecking=no',
     '-o', 'ConnectTimeout=10', 'ubuntu@18.213.66.136',
     'curl -s http://localhost:8000/api/health'],
    capture_output=True, text=True, timeout=10
)
print(f"Port 8000: {r.stdout[:100] if r.stdout else 'TIMEOUT'}")

r = subprocess.run(
    ['ssh', '-i', 'ec2-key.pem', '-o', 'StrictHostKeyChecking=no',
     '-o', 'ConnectTimeout=10', 'ubuntu@18.213.66.136',
     'curl -s http://localhost/api/health'],
    capture_output=True, text=True, timeout=10
)
print(f"Nginx: {r.stdout[:100] if r.stdout else 'TIMEOUT'}")

r = subprocess.run(
    ['ssh', '-i', 'ec2-key.pem', '-o', 'StrictHostKeyChecking=no',
     '-o', 'ConnectTimeout=10', 'ubuntu@18.213.66.136',
     'ps aux | grep \"admin.main\" | grep -v grep | head -2'],
    capture_output=True, text=True, timeout=10
)
print(f"Process: {r.stdout[:80] if r.stdout else 'NOT RUNNING'}")
