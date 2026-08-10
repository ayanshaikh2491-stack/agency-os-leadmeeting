import subprocess, os

os.chdir(r"C:\Users\TAUSHEF\Downloads\int")
KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

cmds = [
    # full log head
    "cat /tmp/pb_import_run2.log | head -25",
    # count duplicates by legacy_id in PB
    "TOKEN=$(curl -s -X POST http://127.0.0.1:8090/api/collections/_superusers/auth-with-password -H 'Content-Type: application/json' -d '{\"identity\":\"admin@tagsagency.local\",\"password\":\"pb-admin-2026-x9\"}' | python3 -c 'import sys,json; print(json.load(sys.stdin).get(\"token\",\"\"))' 2>/dev/null); python3 - <<'EOF' 2>/dev/null
import json,urllib.request
tok=\"$TOKEN\"
def get(c,page):
    u=f\"http://127.0.0.1:8090/api/collections/{c}/records?perPage=200&page={page}&fields=legacy_id\"
    req=urllib.request.Request(u,headers={\"Authorization\":\"Bearer \"+tok})
    return json.load(urllib.request.urlopen(req,timeout=15))
for c in [\"leads\",\"ws_agency__leads\"]:
    seen={};dups=0;total=0;page=1
    while True:
        d=get(c,page);items=d.get(\"items\",[])
        if not items: break
        for it in items:
            lid=str(it.get(\"legacy_id\",\"\"))
            total+=1
            if lid and lid in seen: dups+=1
            seen[lid]=1
        if len(items)<200: break
        page+=1
    print(c,\"total\",total,\"dups\",dups)
EOF",
]
for cmd in cmds:
    print("=" * 20)
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
                        "-o", "ConnectTimeout=10", "-i", KEY, HOST, cmd],
                       capture_output=True, text=True, timeout=90, encoding="utf-8", errors="replace")
    print("rc=", r.returncode)
    print(r.stdout.strip()[:3500])
    if r.stderr.strip():
        print("ERR:", r.stderr.strip()[:400])
