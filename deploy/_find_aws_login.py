import os, glob

roots = [os.path.expanduser("~"), os.environ.get("LOCALAPPDATA", ""), os.environ.get("APPDATA", "")]
seen = set()
for root in roots:
    if not root or not os.path.isdir(root):
        continue
    for f in glob.glob(os.path.join(root, "**", "*aws-login*"), recursive=True):
        if f.lower() not in seen:
            seen.add(f.lower())
            print(f)
    for f in glob.glob(os.path.join(root, "**", "*aws_login*"), recursive=True):
        if f.lower() not in seen:
            seen.add(f.lower())
            print(f)
print("---done---")
