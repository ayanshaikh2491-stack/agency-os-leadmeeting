"""Check EC2 HTTP - non-blocking"""
import urllib.request, json

urls = [
    ("EC2 port 9002 health", "http://18.213.66.136:9002/api/health"),
    ("EC2 port 9002 direct", "http://18.213.66.136:9002/health"),
]

for name, url in urls:
    try:
        r = urllib.request.urlopen(url, timeout=8)
        data = r.read().decode()
        print(f"✅ {name}")
        print(f"   {data[:200]}")
    except Exception as e:
        print(f"❌ {name} — {str(e)[:60]}")
