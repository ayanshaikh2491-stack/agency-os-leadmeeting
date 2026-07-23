"""Fix SBA on EC2 - step by step with binary capture"""
import subprocess, os

KEY = 'C:/Users/TAUSHEF/Downloads/int/ec2-key.pem'
HOST = 'ubuntu@18.213.66.136'

def ssh(cmd_str, timeout=120):
    full = ['ssh', '-i', KEY, '-o', 'StrictHostKeyChecking=no',
            '-o', 'ConnectTimeout=15', '-o', 'UserKnownHostsFile=/dev/null',
            HOST, cmd_str]
    # Don't decode automatically - handle encoding errors
    r = subprocess.run(full, capture_output=True, timeout=timeout)
    out = r.stdout.decode('utf-8', errors='replace')
    err = r.stderr.decode('utf-8', errors='replace')
    if out.strip(): print(out[:500])
    if err.strip() and 'Warning' not in err:
        print('ERR:', err[:300])
    return r.returncode

# 1. Create venv + install
print('=== 1. Venv + pip ===')
ssh('cd /home/ubuntu/sba-backend && python3 -m venv venv && source venv/bin/activate && pip install fastapi uvicorn httpx python-multipart pydantic 2>&1 | tail -3', timeout=180)

# 2. Test import
print('\n=== 2. Test import ===')
ssh('cd /home/ubuntu/sba-backend && source venv/bin/activate && python -c "import sys; sys.path.insert(0,\".\"); from admin.api.models.schemas import HealthResponse; print(\"IMPORT OK\")"', timeout=30)

# 3. Kill old processes, start fresh
print('\n=== 3. Kill old + restart ===')
ssh('pkill -f "admin.main" 2>/dev/null; cd /home/ubuntu/sba-backend && source venv/bin/activate && nohup python -m admin.main > /tmp/sba.log 2>&1 & sleep 4 && curl -s --max-time 5 http://localhost:9002/api/health', timeout=30)

# 4. Log
print('\n=== 4. Log ===')
ssh('tail -20 /tmp/sba.log', timeout=30)

print('\n🎉 Done!')
