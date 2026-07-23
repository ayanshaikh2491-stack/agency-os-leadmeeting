"""Quick import test for CEO agent upgrade."""
import sys
sys.path.insert(0, r"C:\Users\TAUSHEF\Downloads\int")

try:
    from admin.agency.ceo import AgencyCEO, CEO_TOOLS, CEO_SYSTEM_PROMPT
    print(f"Tools count: {len(CEO_TOOLS)}")
    tool_names = [t['function']['name'] for t in CEO_TOOLS]
    print(f"Tool names: {tool_names}")
    print(f"Prompt length: {len(CEO_SYSTEM_PROMPT)} chars")
    ceo = AgencyCEO()
    print("CEO agent created OK")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

try:
    from admin.workspace.manager import (
        store_agent_output, list_pending_reviews, store_review,
        list_reviews, store_error, list_errors
    )
    print("Workspace manager functions OK")
except Exception as e:
    print(f"Workspace manager ERROR: {e}")
    import traceback
    traceback.print_exc()

try:
    from admin.api.routes.ceo import router, _old_router
    routes = [r.path for r in router.routes]
    print(f"CEO routes: {routes}")
except Exception as e:
    print(f"Routes ERROR: {e}")
    import traceback
    traceback.print_exc()
