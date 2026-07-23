"""Check all registered API routes."""
import sys
sys.path.insert(0, r"C:\Users\TAUSHEF\Downloads\int")
from admin.main import app

print("=== All Registered Routes ===")
for route in app.routes:
    if hasattr(route, "path"):
        methods = getattr(route, "methods", set())
        print(f"  {methods or 'GET'} {route.path}")
print(f"\nTotal: {len([r for r in app.routes if hasattr(r, 'path')])} routes")
