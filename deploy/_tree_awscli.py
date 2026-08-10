import os, glob

base = r"C:\Users\TAUSHEF\AppData\Local\Programs\Amazon\AWSCLIV2"
for root, dirs, files in os.walk(base):
    depth = root[len(base):].count(os.sep)
    if depth > 4:
        continue
    rel = os.path.relpath(root, base)
    if rel.count(os.sep) <= 3:
        print(rel)
