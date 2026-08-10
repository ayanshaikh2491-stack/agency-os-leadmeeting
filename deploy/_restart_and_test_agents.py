"""Restart sba + gateway services and test all 7 live agents via gateway."""
import json, os, subprocess, sys, time, urllib.request
sys.path.insert(0, os.getcwd())

KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"
GATEWAY = "http://127.0.0.1:8095"

def run(args, timeout=180, tries=3):
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

print("== restart sba.service ==")
r = ssh("sudo systemctl restart sba.service && sleep 6 && systemctl is-active sba.service")
print((r.stdout or "").strip(), (r.stderr or "").strip()[-300:])

print("== service health (all services) ==")
r = ssh("systemctl is-active sba.service sba-gateway.service sba-autopilot.service sba-chrome.service pocketbase.service")
print((r.stdout or "").strip())

print("== agents list via gateway ==")
try:
    with urllib.request.urlopen(GATEWAY + "/api/agents", timeout=15) as resp:
        print(resp.read().decode()[:800])
except Exception as e:
    print("ERR:", e)

def agent_chat(slug, message):
    body = json.dumps({"message": message, "workspace": "Agency Workspace", "thread_id": "fix-test-" + slug}).encode()
    req = urllib.request.Request(GATEWAY + f"/api/agents/{slug}/chat", data=body,
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            raw = resp.read().decode()
            try:
                d = json.loads(raw)
            except Exception:
                d = {"raw": raw[:400]}
            return d
    except urllib.error.HTTPError as e:
        return {"http_error": e.code, "body": e.read().decode()[:400]}
    except Exception as e:
        return {"err": str(e)[:400]}

AGENTS = ["content-creator", "seo-engine", "ads-runner", "analytics-bot", "social-manager", "website-builder", "memory-agent"]
for slug in AGENTS:
    print(f"\n== {slug} ==")
    out = agent_chat(slug, "hi, one line only: confirm you are online")
    if isinstance(out, dict) and "reply" in out:
        print("OK reply:", str(out["reply"])[:300])
    elif isinstance(out, dict) and "content" in out:
        print("OK content:", str(out["content"])[:300])
    else:
        print("RESULT:", json.dumps(out)[:600])
