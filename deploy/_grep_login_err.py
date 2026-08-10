import zipfile, os, glob

base = r"C:\Users\TAUSHEF\AppData\Local\Programs\Amazon\AWSCLIV2"
# Search for the error string in all python-ish files (py, pyc embedded in zip)
target = "Failed to decode the verification code"
found_in = []

for root, dirs, files in os.walk(base):
    for fn in files:
        p = os.path.join(root, fn)
        try:
            if fn.endswith(".py"):
                with open(p, "r", encoding="utf-8", errors="replace") as f:
                    if target in f.read():
                        found_in.append(p)
        except Exception:
            pass
print("PY HITS:", found_in)

# Search zip files
for z in glob.glob(os.path.join(base, "**", "*.zip"), recursive=True):
    try:
        with zipfile.ZipFile(z) as zf:
            for n in zf.namelist():
                if n.endswith(".py"):
                    try:
                        data = zf.read(n)
                        if target.encode() in data:
                            found_in.append(z + "!" + n)
                    except Exception:
                        pass
    except Exception as e:
        print("zip err", z, e)
print("ZIP HITS:", found_in)
