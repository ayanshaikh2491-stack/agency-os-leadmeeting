"""Verify frontend connects to SBA backend via Vercel."""
import urllib.request, json

FRONTEND_URL = 'https://agency-frontend-seven.vercel.app'

# Test 1: Health endpoint proxy
print("1. Testing health via frontend proxy...")
try:
    r = urllib.request.urlopen(f'{FRONTEND_URL}/api/health', timeout=15)
    data = json.loads(r.read())
    print(f"   ✅ {data}")
except Exception as e:
    print(f"   ❌ {e}")

# Test 2: SBA status via frontend proxy
print("\n2. Testing SBA status via frontend proxy...")
try:
    r = urllib.request.urlopen(f'{FRONTEND_URL}/api/sba/status', timeout=15)
    data = json.loads(r.read())
    print(f"   ✅ SBA status: {data.get('sba', {}).get('status')}")
except Exception as e:
    print(f"   ❌ {e}")

# Test 3: SBA chat via frontend proxy
print("\n3. Testing SBA chat via frontend proxy...")
data = json.dumps({"message": "Hello! Kaise ho?", "session_id": "frontend_test"}).encode()
req = urllib.request.Request(
    f'{FRONTEND_URL}/api/sba/chat',
    data=data, headers={'Content-Type': 'application/json'}, method='POST'
)
try:
    resp = urllib.request.urlopen(req, timeout=60)
    result = json.loads(resp.read())
    print(f"   ✅ Response: {result.get('response', '')[:150]}...")
except Exception as e:
    print(f"   ❌ {e}")

# Test 4: SBA page loads
print("\n4. Testing SBA agent page loads...")
try:
    r = urllib.request.urlopen(f'{FRONTEND_URL}/admin/agents/sba', timeout=15)
    print(f"   ✅ Page loads (status {r.status})")
except Exception as e:
    print(f"   ❌ {e}")
