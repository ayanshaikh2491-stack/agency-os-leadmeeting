import sqlite3
import bcrypt

db = r"C:\Users\TAUSHEF\Downloads\int\deploy\pocketbase\win\pb_data\data.db"
con = sqlite3.connect(db)
cur = con.cursor()
rows = cur.execute("select email, password from _superusers").fetchall()
candidates = [
    "pb-admin-2026-x9",
    '"pb-admin-2026-x9"',
    "pb-admin-2026-x9\r",
    "pb-admin-2026-x9\n",
    "pb-admin-2026-x9 ",
]
for email, pw in rows:
    for c in candidates:
        if bcrypt.checkpw(c.encode(), pw.encode()):
            print("MATCH", email, repr(c))
            break
    else:
        print("no candidate matched", email)
con.close()
