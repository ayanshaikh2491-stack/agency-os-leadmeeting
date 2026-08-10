import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

script = r'''
cd /home/ubuntu/pb_export
python3 - <<'EOF'
import json
n = 0
ints = 0
strs = 0
samples = []
for line in open("public__leads.jsonl", encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    row = json.loads(line)
    n += 1
    ph = row.get("phone")
    if isinstance(ph, (int, float)):
        ints += 1
        if len(samples) < 3:
            samples.append(("INT", row.get("id"), ph))
    elif isinstance(ph, str):
        strs += 1
        if len(samples) < 3:
            samples.append(("STR", row.get("id"), ph))
    else:
        if len(samples) < 3:
            samples.append(("OTHER", row.get("id"), repr(ph)))
print("export total:", n, "int:", ints, "str:", strs)
for s in samples:
    print("  ", s)
EOF
'''

r = subprocess.run(
    ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-i", KEY, HOST, script],
    capture_output=True, text=True, timeout=120,
)
print(r.stdout)
if r.stderr:
    print("STDERR:", r.stderr[:1000])
print("rc=", r.returncode)
