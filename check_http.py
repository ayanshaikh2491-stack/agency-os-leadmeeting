"""Check if EC2 is reachable via HTTP"""
import urllib.request
import json

urls = [
    ("EC2 port 9002", "http://18.213.66.136:9002/api/health"),
    ("EC2 port 9002 root", "http://18.213.66.136:9002/health"),
    ("EC2 port 8000", "http://18.213.66.136:8000/api/health"),
    ("EC2 port 9001", "http://18.213.66.136:9001/api/sba/status"),
]

for name, url in urls:
    try:
        r = urllib.request.urlopen(url, timeout=8)
        data = r.read().decode()
        print(f"✅ {name} — OK")
        print(f"   {data[:200]}")
    except Exception as e:
        print(f"❌ {name} — {str(e)[:60]}")
