import requests, json, subprocess
key = 'ec2-key.pem'
host = 'ubuntu@18.213.66.136'

# Test 1: Agency workspace - Chrome check
print("=== TEST 1: Agency Chrome ===")
r = requests.post('http://18.213.66.136/api/sba/chat',
    json={'workspace_id':'agency','workspace_name':'agency','client_name':'Agency','message':'Chrome mein google.com kholo aur page ka title batao'},
    timeout=120)
data = r.json()
print("Response:", data.get('response','')[:500])

# Start client workspace Chrome daemon
print("\n=== Starting Client Chrome Daemon ===")
subprocess.run(['ssh', '-i', key, '-o', 'StrictHostKeyChecking=no', host,
    'sudo systemctl start sba-chrome@client_realestate 2>&1; sleep 3; sudo systemctl is-active sba-chrome@client_realestate'],
    capture_output=True, text=True, timeout=20)

# Test 2: Client workspace 
print("=== TEST 2: Client Chrome ===")
r = requests.post('http://18.213.66.136/api/sba/chat',
    json={'workspace_id':'client_realestate','workspace_name':'client_realestate','client_name':'Real Estate','message':'Chrome mein google.com kholo aur page ka title batao'},
    timeout=120)
data = r.json()
print("Response:", data.get('response','')[:500])
