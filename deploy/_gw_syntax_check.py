import ast
src = open(r"C:\Users\TAUSHEF\Downloads\int\deploy\pb_gateway.py", encoding="utf-8").read()
ast.parse(src)
print("SYNTAX OK")
# also verify SERVICE_KEY resolution from a fake env
import os, sys
os.environ.pop("SERVICE_KEY", None)
os.environ["PB_ENV_FILE"] = r"C:\Users\TAUSHEF\Downloads\int\deploy\_test.env"
with open(os.environ["PB_ENV_FILE"], "w") as f:
    f.write('SUPABASE_SERVICE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"\n')
ns = {}
exec(compile(src.split("app = FastAPI")[0], "pb_gateway", "exec"), ns)
print("SERVICE_KEY resolved:", ns["SERVICE_KEY"][:12])
