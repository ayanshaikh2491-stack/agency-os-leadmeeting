"""Verify EC2 SBA from external."""
import urllib.request, json
for url in [
    'http://18.213.66.136/api/health',
    'http://18.213.66.136/api/sba/status',
]:
    try:
        r = urllib.request.urlopen(url, timeout=8)
        print(f"✅ {url}")
        print(f"   {json.dumps(json.loads(r.read()), indent=2)[:200]}")
    except Exception as e:
        print(f"❌ {url}: {e}")
