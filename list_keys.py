import os
path = 'C:/Users/TAUSHEF/.ssh'
for f in os.listdir(path):
    if 'agency' in f or 'deploy' in f:
        full = os.path.join(path, f)
        size = os.path.getsize(full)
        print(f'{f} ({size} bytes)')
