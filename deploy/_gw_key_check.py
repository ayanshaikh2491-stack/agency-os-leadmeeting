import os, sys
os.environ.pop("SERVICE_KEY", None)
os.environ["PB_ENV_FILE"] = r"C:\Users\TAUSHEF\Downloads\int\deploy\_test.env"
sys.path.insert(0, r"C:\Users\TAUSHEF\Downloads\int\deploy")
import pb_gateway as g
print("SERVICE_KEY:", g.SERVICE_KEY[:12])
assert g.SERVICE_KEY.startswith("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"), "env key not picked up"
print("ENV KEY RESOLUTION OK")
