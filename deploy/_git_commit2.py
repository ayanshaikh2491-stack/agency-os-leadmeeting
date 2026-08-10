import subprocess, os

os.chdir(r"C:\Users\TAUSHEF\Downloads\int")

def sh(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(">>>", cmd)
    print(r.stdout.strip()[:2000])
    if r.stderr.strip():
        print("ERR:", r.stderr.strip()[:500])
    return r

sh("git add STATE.md && git commit -m 'docs: STATE.md - PocketBase bound to systemd service, PRODUCTION GREEN'")
sh("git log --oneline -1")
