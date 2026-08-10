import urllib.request, json
r = urllib.request.urlopen("http://127.0.0.1:8095/api/health", timeout=5)
print(json.load(r))
