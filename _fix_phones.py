import json, re, os, subprocess

BASE = r"C:\Users\TAUSHEF\Downloads\int"
KEY = os.path.join(BASE, "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=120):
    full = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10",
            "-i", KEY, HOST, cmd]
    r = subprocess.run(full, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return r

lines = [json.loads(l) for l in open(os.path.join(BASE, "data", "sba_maps_leads_live.jsonl"), encoding="utf-8")]

phone_re = re.compile(r'\+?1?[\s.-]?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}')

def extract_phone(lead):
    if lead.get("phone"):
        return lead["phone"]
    text = lead.get("text", "") + " " + lead.get("address", "")
    m = phone_re.search(text)
    if m:
        raw = m.group(0)
        digits = re.sub(r'\D', '', raw)
        if len(digits) == 10:
            return "+1" + digits
        if len(digits) == 11 and digits.startswith("1"):
            return "+" + digits
    return ""

updated = 0
updates = []
for i, l in enumerate(lines):
    ph = extract_phone(l)
    if ph and not l.get("phone"):
        l["phone"] = ph
        updates.append((l["name"], ph))
        updated += 1

print("extracted phones for:", updated)

# Update the JSONL files
good_names = set()
good_path = os.path.join(BASE, "data", "sba_maps_leads_good.jsonl")
if os.path.exists(good_path):
    for line in open(good_path, encoding="utf-8"):
        good_names.add(json.loads(line)["name"])

# Write updated live file
with open(os.path.join(BASE, "data", "sba_maps_leads_live.jsonl"), "w", encoding="utf-8") as f:
    for l in lines:
        f.write(json.dumps(l, ensure_ascii=False) + "\n")

# Write updated good file (fill phones from live)
good_lines = []
for line in open(good_path, encoding="utf-8"):
    gl = json.loads(line)
    for l in lines:
        if l["name"] == gl["name"] and l.get("phone") and not gl.get("phone"):
            gl["phone"] = l["phone"]
            break
    good_lines.append(gl)
with open(good_path, "w", encoding="utf-8") as f:
    for gl in good_lines:
        f.write(json.dumps(gl, ensure_ascii=False) + "\n")

print("JSONL files updated")

# Generate UPDATE SQL
def esc(v):
    return "'" + str(v).replace("'", "''") + "'"

sql_lines = ["BEGIN;"]
for name, ph in updates:
    sql_lines.append(f"UPDATE leads SET phone = {esc(ph)}, updated_at = now() WHERE name = {esc(name)} AND (phone IS NULL OR phone = '');")
sql_lines.append("COMMIT;")
sql = "\n".join(sql_lines)
sql_path = os.path.join(BASE, "_leads_phone.sql")
with open(sql_path, "w", encoding="utf-8") as f:
    f.write(sql)
print("SQL:", len(updates), "updates,", os.path.getsize(sql_path), "bytes")

# Upload and run
scp = ["scp", "-o", "StrictHostKeyChecking=no", "-i", KEY, sql_path, HOST + ":/tmp/leads_phone.sql"]
r = subprocess.run(scp, capture_output=True, text=True, timeout=120, encoding="utf-8", errors="replace")
print("SCP rc:", r.returncode)

r2 = ssh("docker cp /tmp/leads_phone.sql supabase-db:/tmp/ && docker exec supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 -f /tmp/leads_phone.sql 2>&1 | tail -4")
print(r2.stdout[:800])
if r2.stderr.strip():
    print("ERR:", r2.stderr[-400:])

r3 = ssh("docker exec supabase-db psql -U postgres -d postgres -t -c \"select count(*) filter (where phone <> '') as with_phone, count(*) as total from leads;\"")
print("with phone now:", r3.stdout[:200])
