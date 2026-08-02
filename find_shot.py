import tempfile, glob, os
t = tempfile.gettempdir()
print("tmp:", t)
for f in glob.glob(os.path.join(t, "sba_shot_*.png")):
    print("FOUND:", f)
