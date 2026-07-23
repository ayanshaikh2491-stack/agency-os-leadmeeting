import requests, json

# Fresh workspace - no previous conversation
payload = {
    'workspace_id': 'fresh',
    'workspace_name': 'Fresh Agency',
    'client_name': 'Test',
    'message': 'LinkedIn.com pe jao aur dekho kya dikh raha hai page pe'
}
r = requests.post('http://18.213.66.136/api/sba/chat', json=payload, timeout=120)
print("Status:", r.status_code)
data = r.json()
print("Response:", data.get('response', '')[:1000])
if data.get('thinking_phases'):
    print("\nPhases:", json.dumps(data['thinking_phases'], indent=2)[:1000])
