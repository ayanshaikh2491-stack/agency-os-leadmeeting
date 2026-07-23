import requests, json, sys

msg = sys.argv[1] if len(sys.argv) > 1 else "apna Chrome browser check kar ke batao kya haal hai"
r = requests.post('http://18.213.66.136/api/sba/chat',
    json={'workspace_id':'test','workspace_name':'Test Agency','client_name':'Acme Corp','message':msg},
    timeout=120)
print("Status:", r.status_code)
data = r.json()
if data.get('thinking_phases'):
    print("\nThinking:", json.dumps(data['thinking_phases'], indent=2)[:1500])
print("\nResponse:", data.get('response', ''))
