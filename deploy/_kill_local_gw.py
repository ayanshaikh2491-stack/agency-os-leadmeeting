import subprocess, os, signal, sys, time, urllib.request, json

os.chdir(r"C:\Users\TAUSHEF\Downloads\int\deploy")

def sh(cmd, timeout=60):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(">>>", cmd)
    print(r.stdout.strip()[:2000])
    if r.stderr.strip():
        print("ERR:", r.stderr.strip()[:400])
    return r

# kill any existing local gateway on 8095
sh("python -c \"import subprocess,sys; p=subprocess.run(['powershell','-Command','Get-NetTCPConnection -LocalPort 8095 -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess'],capture_output=True,text=True); print(p.stdout.strip())\"")
