"""Drive aws login --remote with controlled stdin.
Writes the URL to _aws_url.txt, waits for _aws_code.txt, feeds code.
Usage: python _aws_login_driver.py
"""
import subprocess
import sys
import time
import os

CODE_FILE = os.path.join(os.getcwd(), "deploy", "_aws_code.txt")
URL_FILE = os.path.join(os.getcwd(), "deploy", "_aws_url.txt")

# remove stale files
for f in (CODE_FILE, URL_FILE):
    if os.path.exists(f):
        os.remove(f)

proc = subprocess.Popen(
    ["aws", "login", "--profile", "aws2", "--remote"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
)

# read until the prompt (URL + "Enter the authorization code")
buf = ""
while True:
    chunk = proc.stdout.read(1)
    if not chunk:
        break
    buf += chunk
    if "authorization code" in buf:
        break
    if len(buf) > 20000:
        break

print(buf)
with open(URL_FILE, "w", encoding="utf-8") as f:
    f.write(buf)

# wait for the code file (created when user pastes code here)
deadline = time.time() + 3600
while time.time() < deadline:
    if os.path.exists(CODE_FILE):
        try:
            code = open(CODE_FILE, encoding="utf-8").read().strip()
        except Exception:
            code = ""
        if code:
            proc.stdin.write(code + "\n")
            proc.stdin.flush()
            break
    if proc.poll() is not None:
        print("PROCESS EXITED EARLY rc=", proc.returncode)
        break
    time.sleep(2)

# drain remaining output
try:
    rest = proc.stdout.read()
    print(rest)
except Exception as e:
    print("read err:", e)

rc = proc.wait(timeout=30)
print("FINAL rc=", rc)
