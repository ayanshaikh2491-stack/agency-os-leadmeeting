import os, glob

roots = [os.path.expanduser("~") + os.sep + ".aws",
         os.path.expanduser("~") + os.sep + ".aws-login",
         os.environ.get("LOCALAPPDATA", ""),
         os.environ.get("APPDATA", "")]
for root in roots:
    if not root or not os.path.isdir(root):
        print("MISS", root)
        continue
    print("ROOT", root)
    for f in glob.glob(os.path.join(root, "**", "*"), recursive=True):
        try:
            if os.path.isfile(f):
                print("  ", f, os.path.getsize(f))
        except OSError:
            pass
print("done")
