import sqlite3

db = r"C:\Users\TAUSHEF\Downloads\int\deploy\pocketbase\win\pb_data\data.db"
con = sqlite3.connect(db)
cur = con.cursor()
rows = cur.execute("select email, password from _superusers").fetchall()
print("superusers:")
for email, pw in rows:
    print(" ", email, pw[:20], "...")

# verify latest admin@tagsagency.local hash
try:
    import bcrypt
    for email, pw in rows:
        ok = bcrypt.checkpw(b"pb-admin-2026-x9", pw.encode())
        print("  match pb-admin-2026-x9 for", email, "->", ok)
except Exception as e:
    print("bcrypt err:", e)
con.close()
