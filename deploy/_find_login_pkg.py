import os, glob

base = r"C:\Users\TAUSHEF\AppData\Local\Programs\Amazon\AWSCLIV2"
# The CLI bundles a python runtime; look for login-related package dirs
for root, dirs, files in os.walk(base):
    depth = root[len(base):].count(os.sep)
    if depth > 3:
        continue
    for d in dirs:
        if "login" in d.lower():
            print("DIR:", os.path.join(root, d))
    for fn in files:
        if "login" in fn.lower():
            print("FILE:", os.path.join(root, fn))
