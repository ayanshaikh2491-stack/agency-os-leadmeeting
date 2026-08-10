"""Test all 7 agents against the backend directly on port 8000 (EC2)."""
import json, os, subprocess, sys, time, urllib.request
sys.path.insert(0, os.getcwd())

KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def run(args, timeout=120, tries=3):
    last = None
    for i in range(tries):
        try:
            r = subprocess.run(args, capture_output=True, text=True, timeout=timeout,
                               encoding="utf-8", errors="replace")
            if r.returncode == 0 or r.stdout.strip():
                return r
            last = r
        except Exception as e:
            last = e
        time.sleep(3)
    return last

ssh = lambda cmd: run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
                       "-o", "ConnectTimeout=20", "-i", KEY, HOST, cmd])

BASE = "http://127.0.0.1:8000"

def post(path, body, timeout=120):
    data = json.dumps(body).encode()
    req = urllib.request.Request(BASE + path, data=data,
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode()
            try:
                return resp.status, json.loads(raw)
            except Exception:
                return resp.status, {"raw": raw[:400]}
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:400]
    except Exception as e:
        return -1, {"err": str(e)[:400]}

def get(path):
    req = urllib.request.Request(BASE + path)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read().decode()[:600]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:400]
    except Exception as e:
        return -1, str(e)[:300]

print("== GET /api/agents ==")
print(get("/api/agents"))

AGENTS = ["content-creator", "seo-engine", "ads-runner", "analytics-bot", "social-manager", "website-builder", "memory-agent"]
for slug in AGENTS:
    print(f"\n== {slug} ==")
    st, d = post(f"/api/agents/{slug}/chat", {"message": "hi, reply in one line", "client_name": "Agency Workspace"})
    if isinstance(d, dict):
        resp = d.get("data", {}).get("response") or d.get("reply") or d.get("response")
        if resp:
            print("OK:", str(resp)[:250])
        else:
            print("RESULT", st, json.dumps(d)[:400])
    else:
        print("RESULT", st, str(d)[:400])
