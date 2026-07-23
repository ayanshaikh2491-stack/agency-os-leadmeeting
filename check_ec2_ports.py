"""Check EC2 ports and fix SBA deployment."""
import subprocess, tempfile, os

key = 'ec2-key.pem'
host = 'ubuntu@18.213.66.136'
ssh = ['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no',
       '-o', 'ConnectTimeout=10']

def run_script(script_content):
    """Write script with LF endings and run via SSH."""
    tf = tempfile.NamedTemporaryFile(mode='wb', suffix='.sh', delete=False)
    tf.write(script_content.encode('utf-8'))
    tf.close()
    
    r = subprocess.run(
        ssh + [host, 'cat > /tmp/ec2_cmd.sh'],
        stdin=open(tf.name, 'rb'), capture_output=True, text=True, timeout=15
    )
    os.unlink(tf.name)
    
    r = subprocess.run(
        ssh + [host, 'bash /tmp/ec2_cmd.sh'],
        capture_output=True, text=True, timeout=30
    )
    return r

# Check what's on port 8000 and 9002
r = run_script(
    '#!/bin/bash\n'
    'echo "=== Ports ==="\n'
    'ss -tlnp | grep -E "8000|9002" || echo "No ports 8000/9002"\n'
    'echo "=== Security Group ==="\n'
    'curl -s http://169.254.169.254/latest/meta-data/security-groups 2>/dev/null || echo "No metadata"\n'
)

print(r.stdout[:500])
if r.stderr.strip(): print(f"ERR: {r.stderr[:200]}")
