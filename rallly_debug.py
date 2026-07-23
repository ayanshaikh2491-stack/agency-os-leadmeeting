import subprocess, requests
key = 'ec2-key.pem'
host = 'ubuntu@18.213.66.136'

# Try with HTTP/1.0
r = subprocess.run(['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no', host,
    'curl -v --http1.0 --max-time 10 http://127.0.0.1:3001/ 2>&1 | head -40'],
    capture_output=True, text=True, timeout=15)
print("HTTP/1.0:", r.stdout[-1000:])

# Check docker log while connecting
print("\n=== Logs during connection ===")
r = subprocess.run(['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no', host,
    'sudo docker logs rallly-rallly-1 --tail=5 2>&1; echo; curl -s --max-time 3 http://127.0.0.1:3001/ 2>&1; sleep 1; sudo docker logs rallly-rallly-1 --tail=5 2>&1'],
    capture_output=True, text=True, timeout=20)
print(r.stdout[-1000:])

# Try from local machine directly
try:
    r2 = requests.get('http://18.213.66.136:3001/', timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
    print(f"\nExternal status: {r2.status_code}")
    print(f"External body: {r2.text[:200]}")
except Exception as e:
    print(f"\nExternal error: {e}")
