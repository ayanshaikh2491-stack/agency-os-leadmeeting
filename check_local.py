"""Check local backend health"""
import urllib.request
try:
    r = urllib.request.urlopen("http://localhost:9002/api/health", timeout=5)
    print("Status:", r.status)
    print("Body:", r.read().decode()[:300])
except Exception as e:
    print("Error:", e)
