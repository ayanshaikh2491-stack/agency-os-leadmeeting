import os, json, glob, time
cache_dir = os.path.expanduser("~") + os.sep + ".aws" + os.sep + "login" + os.sep + "cache"
for f in sorted(glob.glob(os.path.join(cache_dir, "*")), key=os.path.getmtime, reverse=True):
    print("FILE:", os.path.basename(f), "mtime:", time.strftime("%Y-%m-%d %H:%M:%SZ", time.gmtime(os.path.getmtime(f))), "size:", os.path.getsize(f))
    try:
        with open(f, "r", encoding="utf-8", errors="replace") as fh:
            data = json.load(fh)
        at = data.get("accessToken", {})
        print("  account:", at.get("accountId"), "expires:", at.get("expiresAt"))
    except Exception as e:
        print("  err", e)
