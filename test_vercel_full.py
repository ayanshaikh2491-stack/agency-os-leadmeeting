"""Verify frontend connects to SBA backend via Vercel (after fix)."""
import urllib.request, json

FRONTEND_URL = 'https://agency-frontend-seven.vercel.app'

# Test 1: Health
print("1. Health via frontend proxy...")
try:
    r = urllib.request.urlopen(f'{FRONTEND_URL}/api/health', timeout=15)
    print(f"   ✅ {json.loads(r.read())}")
except Exception as e:
    print(f"   ❌ {e}")

# Test 2: SBA status
print("\n2. SBA status via frontend proxy...")
try:
    r = urllib.request.urlopen(f'{FRONTEND_URL}/api/sba/status', timeout=15)
    data = json.loads(r.read())
    print(f"   ✅ Status: {data.get('sba', {}).get('status')}")
except Exception as e:
    print(f"   ❌ {e}")

# Test 3: SBA chat (the important one - was 503 earlier)
print("\n3. SBA chat via frontend proxy...")
data = json.dumps({"message": "Kaise ho bhai? Test kar raha hoon frontend se!", "session_id": "frontend_test_2"}).encode()
req = urllib.request.Request(
    f'{FRONTEND_URL}/api/sba/chat',
    data=data, headers={'Content-Type': 'application/json'}, method='POST'
)
try:
    resp = urllib.request.urlopen(req, timeout=90)
    result = json.loads(resp.read())
    response_text = result.get('response', '')
    print(f"   ✅ Response ({len(response_text)} chars): {response_text[:200]}...")
    phases = result.get('thinking_phases', [])
    if phases:
        print(f"   🧠 Thinking phases: {len(phases)}")
        for p in phases:
            print(f"       - {p['phase']}")
except Exception as e:
    print(f"   ❌ {e}")

# Test 4: SBA agent page loads
print("\n4. SBA agent page...")
try:
    r = urllib.request.urlopen(f'{FRONTEND_URL}/admin/agents/sba', timeout=15)
    print(f"   ✅ Page loads (status {r.status})")
except Exception as e:
    print(f"   ❌ {e}")

print("\n✅ Done!")
