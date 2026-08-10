import os, glob, zipfile

base = r"C:\Users\TAUSHEF\AppData\Local\Programs\Amazon\AWSCLIV2"
targets = [b"Failed to decode the verification code", b"decode the verification code", b"verification code"]
found = set()

for root, dirs, files in os.walk(base):
    for fn in files:
        p = os.path.join(root, fn)
        try:
            if os.path.getsize(p) > 50_000_000:
                continue
            with open(p, "rb") as f:
                data = f.read()
            for t in targets:
                if t in data:
                    found.add(p)
                    break
        except Exception:
            pass

for z in glob.glob(os.path.join(base, "**", "*.zip"), recursive=True):
    try:
        with zipfile.ZipFile(z) as zf:
            for n in zf.namelist():
                try:
                    data = zf.read(n)
                    for t in targets:
                        if t in data:
                            found.add(z + "!" + n)
                            break
                except Exception:
                    pass
    except Exception:
        pass

for f in sorted(found):
    print(f)
print("total:", len(found))
