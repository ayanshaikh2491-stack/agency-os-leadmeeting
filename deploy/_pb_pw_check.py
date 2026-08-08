import hashlib

# bcrypt hash from db
h = "$2a$10$cVV01pTcX.KPVCfjksN/9.wierwTeqEoGuWtnL/AV0lEUT4mz0yHS"
pwd = b"pb-admin-2026-x9"

# try bcrypt if available
try:
    import bcrypt
    print("bcrypt match:", bcrypt.checkpw(pwd, h.encode()))
except ImportError:
    try:
        import passlib.hash as ph
        print("passlib match:", ph.bcrypt.verify(pwd.decode(), h))
    except ImportError:
        print("no bcrypt lib; try pip install bcrypt")
        import sys
        print(sys.executable)
