import sqlite3

db = r"C:\Users\TAUSHEF\Downloads\int\deploy\pocketbase\win\pb_data\data.db"
con = sqlite3.connect(db)
cur = con.cursor()
# WAL mode: need to read committed data from wal
try:
    cur.execute("PRAGMA wal_checkpoint(FULL)")
except Exception as e:
    print("checkpoint err:", e)
tables = [r[0] for r in cur.execute("select name from sqlite_master where type='table'")]
print("tables:", tables)
for t in tables:
    if "superuser" in t.lower() or "user" in t.lower():
        cols = [c[1] for c in cur.execute(f"PRAGMA table_info({t})")]
        print(t, "cols:", cols)
        try:
            rows = cur.execute(f"select * from {t}").fetchall()
            for r in rows:
                # mask token
                rr = list(r)
                print(t, "row:", [ (str(x)[:60] + '...' if x and len(str(x)) > 60 else x) for x in rr])
        except Exception as e:
            print("  err", e)
con.close()
