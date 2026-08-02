import urllib.request

req = urllib.request.Request("http://18.213.66.136:8050/studio/", headers={"User-Agent": "Mozilla/5.0"})
try:
    r = urllib.request.urlopen(req, timeout=20)
    print("STATUS:", r.status)
    print("FINAL URL:", r.geturl())
except Exception as e:
    print("ERR:", e)
