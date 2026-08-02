import json, subprocess, tempfile, os

BASE = r"C:\Users\TAUSHEF\Downloads\int"
KEY = os.path.join(BASE, "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=120):
    full = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10",
            "-i", KEY, HOST, cmd]
    r = subprocess.run(full, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return r

# Load leads
candidates = [json.loads(l) for l in open(os.path.join(BASE, "data", "sba_maps_leads_live.jsonl"), encoding="utf-8")]
good_names = set()
for l in open(os.path.join(BASE, "data", "sba_maps_leads_good.jsonl"), encoding="utf-8"):
    good_names.add(json.loads(l)["name"])
print("candidates:", len(candidates), "good:", len(good_names))

def esc(v):
    if v is None:
        return "NULL"
    return "'" + str(v).replace("'", "''") + "'"

# Build insert values
rows = []
for c in candidates:
    st = "good" if c.get("name") in good_names else "candidate"
    vals = (
        esc(c.get("name")), "true" if c.get("has_website") else "false",
        esc(c.get("phone")), esc(c.get("category")), esc(c.get("city_state")),
        esc(c.get("address")), esc(c.get("href")), esc(c.get("text")),
        esc(c.get("mode")), esc(c.get("website_status")), esc(st),
        "'" + json.dumps(c, ensure_ascii=False).replace("'", "''") + "'"
    )
    rows.append("(" + ", ".join(vals) + ")")

# Chunk inserts (100 per statement)
sql_path = os.path.join(BASE, "_leads_insert.sql")
with open(sql_path, "w", encoding="utf-8") as f:
    f.write("BEGIN;\n")
    for i in range(0, len(rows), 100):
        chunk = rows[i:i+100]
        f.write("INSERT INTO leads (name, has_website, phone, category, city_state, address, href, text, mode, website_status, status, raw) VALUES\n")
        f.write(",\n".join(chunk))
        f.write(";\n")
    f.write("COMMIT;\n")
print("SQL written:", sql_path, os.path.getsize(sql_path), "bytes,", len(rows), "rows")

# Upload and run
scp = ["scp", "-o", "StrictHostKeyChecking=no", "-i", KEY, sql_path, HOST + ":/tmp/leads_insert.sql"]
r = subprocess.run(scp, capture_output=True, text=True, timeout=120, encoding="utf-8", errors="replace")
print("SCP rc:", r.returncode)

r2 = ssh("docker cp /tmp/leads_insert.sql supabase-db:/tmp/ && docker exec supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 -f /tmp/leads_insert.sql 2>&1 | tail -8")
print("\n=== INSERT RESULT ===")
print(r2.stdout[:1500])
if r2.stderr.strip():
    print("ERR:", r2.stderr[-500:])

# Verify count
r3 = ssh("docker exec supabase-db psql -U postgres -d postgres -t -c 'select status, count(*) from leads group by status;'")
print("\n=== LEAD COUNTS ===")
print(r3.stdout[:800])
