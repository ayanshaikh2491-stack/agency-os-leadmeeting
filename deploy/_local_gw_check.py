import subprocess, os, sys, time

os.chdir(r"C:\Users\TAUSHEF\Downloads\int")

def sh(cmd, timeout=120):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(">>>", cmd)
    print(r.stdout.strip()[:3000])
    if r.stderr.strip():
        print("ERR:", r.stderr.strip()[:600])
    return r

# 1. Is local gateway running? (from last session, it was on 8095)
r = sh("python -c \"import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8095/health', timeout=5).read().decode())\"")
# 2. Syntax check the patched gateway
r = sh("python -m py_compile deploy/pb_gateway.py && echo SYNTAX_OK")
