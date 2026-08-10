"""Check lead sourcing: pass_summary stats + new_leads_found in last passes."""
import os, subprocess, sys, json, time
sys.path.insert(0, os.getcwd())

KEY = os.path.join(os.getcwd(), "ec2-key.pem")
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=60, tries=3):
    for i in range(tries):
        try:
            r = subprocess.run(
                ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
                 "-o", "ConnectTimeout=10", "-i", KEY, HOST, cmd],
                capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
            if r.returncode == 0 or r.stdout.strip():
                return r
        except Exception:
            pass
        time.sleep(3)
    return None

# pass_summary lines from log
r = ssh("cd /home/ubuntu/sba-backend && grep pass_summary sba_reasoning_agency.log | tail -6")
print("PASS SUMMARIES:")
if r and r.stdout.strip():
    for line in r.stdout.strip().splitlines():
        try:
            d = json.loads(line)
            s = d.get("stats", {})
            print(f"  {d.get('ts','')[:19]} | new_leads={s.get('new_leads_found')} emails_sent={s.get('emails_sent')} no_email={s.get('no_email')} deferred={s.get('deferred_to_business_hours')}")
        except Exception:
            print("  RAW:", line[:120])
else:
    print("  none / SSH_FAIL")

# also check any lead_found/lead_sourced events
r2 = ssh("cd /home/ubuntu/sba-backend && grep -E 'lead_found|lead_sourced|scrape' sba_reasoning_agency.log | tail -6")
print("LEAD EVENTS:")
print(r2.stdout.strip()[-1200:] if r2 and r2.stdout.strip() else "  none")
