import os, glob

base = r"C:\Users\TAUSHEF\AppData\Local\Programs\Amazon\AWSCLIV2"
targets = [b"verification code", b"verification_code", b"Failed to decode"]
hits = []
for root, dirs, files in os.walk(base):
    # skip botocore data (huge, irrelevant)
    if os.sep + "botocore" + os.sep + "data" in root:
        continue
    for fn in files:
        p = os.path.join(root, fn)
        try:
            if not (fn.endswith(".py") or fn.endswith(".pyc")):
                continue
            with open(p, "rb") as f:
                data = f.read()
            for t in targets:
                if t in data:
                    hits.append((p, t.decode()))
                    break
        except Exception:
            pass
for p, t in hits:
    print(t, "->", p)
print("total:", len(hits))
