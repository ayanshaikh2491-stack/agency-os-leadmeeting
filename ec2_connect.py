import subprocess, os, shutil

key_src = 'C:/Users/TAUSHEF/.ssh/agency-backend-key-20260521.pem'
key_dst = 'C:/Users/TAUSHEF/Downloads/int/ec2-key.pem'
shutil.copy2(key_src, key_dst)
os.chmod(key_dst, 0o600)
print('Key ready')

cmd = ['ssh', '-i', key_dst, '-o', 'StrictHostKeyChecking=no', '-o', 'UserKnownHostsFile=/dev/null', 'ubuntu@18.213.66.136',
       'hostname && uptime && echo "" && echo "== SERVICES ==" && ss -tlnp | grep -E "8000|9001|9002" || echo "(none)" && echo "== PYTHON ==" && python3 --version 2>&1 && echo "== DISK ==" && df -h / | tail -1']

r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
print(r.stdout)
if r.stderr:
    print('STDERR:', r.stderr[:200])
print('EXIT:', r.returncode)
