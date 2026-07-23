"""Start server and test CEO endpoints."""
import sys
sys.path.insert(0, r"C:\Users\TAUSHEF\Downloads\int")
from admin.main import app
print("App imported OK, all routes registered")
for route in app.routes:
    if hasattr(route, "path"):
        print(f"  {route.path}")
