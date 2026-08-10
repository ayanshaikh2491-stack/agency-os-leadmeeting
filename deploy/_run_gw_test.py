import subprocess, os

os.chdir(r"C:\Users\TAUSHEF\Downloads\int\deploy")
env = dict(os.environ)
env["GW_BASE"] = "http://127.0.0.1:8095"
env["GW_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
r = subprocess.run([os.sys.executable, "_pb_gw_test.py"], capture_output=True, text=True, timeout=180, encoding="utf-8", errors="replace", env=env)
print(r.stdout.strip()[:4000])
if r.stderr.strip():
    print("ERR:", r.stderr.strip()[:800])
