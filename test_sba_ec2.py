"""Test SBA chat on EC2."""
import urllib.request, json

data = json.dumps({
    "message": "Hello! Kaise ho? Just a quick test.",
    "session_id": "ec2_test"
}).encode()

r = urllib.request.Request(
    'http://18.213.66.136/api/sba/chat',
    data=data,
    headers={'Content-Type': 'application/json'},
    method='POST'
)

try:
    resp = urllib.request.urlopen(r, timeout=30)
    result = json.loads(resp.read())
    print(f"✅ Chat response received")
    print(f"Response: {result.get('response', '')[:200]}...")
    print(f"Phases: {len(result.get('thinking_phases', []))}")
except Exception as e:
    print(f"❌ Chat failed: {e}")
