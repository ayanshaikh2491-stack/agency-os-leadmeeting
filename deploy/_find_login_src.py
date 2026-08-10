import glob, os, zipfile

base = r"C:\Users\TAUSHEF\AppData\Local\Programs\Amazon\AWSCLIV2"
hits = []
for f in glob.glob(os.path.join(base, "**", "*"), recursive=True):
    if "login" in os.path.basename(f).lower():
        hits.append(f)
for h in hits[:60]:
    print(h)
# Also check the bundled python zip for login modules
for z in glob.glob(os.path.join(base, "**", "*.zip"), recursive=True):
    print("ZIP:", z)
    try:
        with zipfile.ZipFile(z) as zf:
            for n in zf.namelist():
                if "login" in n.lower() and n.endswith(".py"):
                    print("   ", n)
    except Exception as e:
        print("    err", e)
