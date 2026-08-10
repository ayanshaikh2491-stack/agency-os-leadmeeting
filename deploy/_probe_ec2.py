import socket

host = "18.213.66.136"
for port in (8000, 8090, 8095, 22):
    s = socket.socket()
    s.settimeout(4)
    try:
        r = s.connect_ex((host, port))
        print(f"port {port}: {'OPEN' if r == 0 else 'closed/' + str(r)}")
    except Exception as e:
        print(f"port {port}: error {e}")
    finally:
        s.close()
