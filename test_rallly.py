import subprocess
key = 'ec2-key.pem'
host = 'ubuntu@18.213.66.136'

# Test curl with verbose output
r = subprocess.run(['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no', host,
    'curl -v --max-time 10 http://127.0.0.1:3001/ 2>&1 | head -30'],
    capture_output=True, text=True, timeout=30)
print(r.stdout[-1500:])

# Also try different path
print("\n=== Try /api/health ===")
r = subprocess.run(['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no', host,
    'curl -v --max-time 10 http://127.0.0.1:3001/api/health 2>&1 | head -30'],
    capture_output=True, text=True, timeout=30)
print(r.stdout[-1500:])

# Check logs for errors
print("\n=== Error logs ===")
r = subprocess.run(['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no', host,
    'sudo docker compose -f /home/ubuntu/rallly/docker-compose.yml logs --tail=20 rallly 2>&1 | grep -i error || echo "no errors"'],
    capture_output=True, text=True, timeout=30)
print(r.stdout[-1000:])

# Check if port is listening
print("\n=== Port check ===")
r = subprocess.run(['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no', host,
    'sudo ss -tlnp | grep 3001; echo ---; sudo iptables -L DOCKER -n 2>/dev/null | head -5 || true'],
    capture_output=True, text=True, timeout=15)
print(r.stdout[-500:])

# Try from inside container
print("\n=== Inside container test ===")
r = subprocess.run(['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no', host,
    'sudo docker exec rallly-rallly-1 curl -s -o /dev/null -w %{http_code} --max-time 5 http://localhost:3000/ 2>&1 || echo exit_fail'],
    capture_output=True, text=True, timeout=15)
print(r.stdout[-500:])
