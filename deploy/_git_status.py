import subprocess, os

os.chdir(r"C:\Users\TAUSHEF\Downloads\int")

def sh(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(">>>", cmd)
    print(r.stdout.strip()[:3000])
    if r.stderr.strip():
        print("ERR:", r.stderr.strip()[:800])
    return r

sh("git status --short | head -40")
sh("git log --oneline -3")
