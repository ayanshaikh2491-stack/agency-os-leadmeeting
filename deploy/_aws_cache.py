import os, json, glob
cache_dir = os.path.expanduser("~") + os.sep + ".aws" + os.sep + "login" + os.sep + "cache"
print("CACHE DIR:", cache_dir)
for f in sorted(glob.glob(os.path.join(cache_dir, "*"))):
    print("FILE:", f, os.path.getsize(f))
    try:
        with open(f, "r", encoding="utf-8", errors="replace") as fh:
            data = json.load(fh)
        print(json.dumps(data, indent=1)[:1500])
    except Exception as e:
        print("  (not json:", e, ")")
