import urllib.request

for url in ["https://agency-frontend-seven.vercel.app", "https://agency-frontend-jr7bvidxa-ayanshaikh2491-stacks-projects.vercel.app"]:
    print("=== ", url)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        resp = urllib.request.urlopen(req, timeout=20)
        print("status:", resp.status, "final:", resp.geturl())
        body = resp.read(3000).decode("utf-8", "replace")
        print(body[:1200])
    except urllib.error.HTTPError as e:
        print("HTTPError:", e.code, e.headers.get("Location"))
    except Exception as e:
        print("ERR:", type(e).__name__, str(e)[:200])
