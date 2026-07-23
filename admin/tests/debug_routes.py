"""Debug: Check if routes are being registered."""
import sys
sys.path.insert(0, r"C:\Users\TAUSHEF\Downloads\int")

# Check if ceo routes module has routes
from admin.api.routes.ceo import router, _old_router
print(f"CEO router prefix: {router.prefix}")
print(f"CEO router routes: {len(router.routes)}")
for r in router.routes:
    if hasattr(r, 'path'):
        print(f"  {r.path}")

print(f"\nLegacy router prefix: {_old_router.prefix}")
print(f"Legacy router routes: {len(_old_router.routes)}")
for r in _old_router.routes:
    if hasattr(r, 'path'):
        print(f"  {r.path}")
