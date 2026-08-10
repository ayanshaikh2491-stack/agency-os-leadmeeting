import importlib.util

for m in ["fastapi", "uvicorn", "httpx"]:
    print(m, "->", bool(importlib.util.find_spec(m)))
