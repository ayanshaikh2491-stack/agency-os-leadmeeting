import sys
sys.path.insert(0, r"C:\Users\TAUSHEF\Downloads\int")
from admin.api.routes import ceo as ceo_routes
from admin.agency.ceo import AgencyCEO, build_ceo_graph

g = build_ceo_graph()
print("graph OK, checkpointer:", type(g.checkpointer).__name__)
ceo_obj = AgencyCEO()
print("AgencyCEO OK, thread:", ceo_obj._thread_id)
print("route /api/ceo/chat present:", any(getattr(r, "path", "") == "/api/ceo/chat" for r in ceo_routes.router.routes))
print("ALL_IMPORTS_OK")
