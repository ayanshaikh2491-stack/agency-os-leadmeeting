"""Verify EC2 backend from outside."""
import urllib.request, json

# Test through nginx (port 80)
urls = [
    'http://18.213.66.136/api/health',
    'http://18.213.66.136/api/sba/status',
]

for url in urls:
    try:
        r = urllib.request.urlopen(url, timeout=10)
        data = json.loads(r.read())
        print(f"✅ {url}: {json.dumps(data, indent=2)[:200]}")
    except Exception as e:
        print(f"❌ {url}: {e}")
