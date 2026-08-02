import json, subprocess, sys

prompt = (
    "Meri agency local US businesses ke liye SEO aur website services bechti hai. "
    "Google Maps se 100 leads dhoondo - aise local businesses jinke paas "
    "website nahi hai ya purana/kharab website hai aur unhe SEO ki zaroorat hai. "
    "Chrome use karke Google Maps par search karo aur businesses ki details "
    "(naam, category, location, phone, website presence) collect karo."
)

cmd = [sys.executable, "-u", "admin/tests/live/live_sba_direct.py", prompt]
proc = subprocess.run(cmd, cwd=".", capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
print(proc.stdout)
if proc.stderr.strip():
    print("=== STDERR ===")
    print(proc.stderr[-4000:])
print("EXIT=", proc.returncode)
