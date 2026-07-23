"""Set Vercel env vars and deploy frontend."""
import subprocess, os, tempfile

os.chdir(r'C:\Users\TAUSHEF\Downloads\int\agency-frontend')

# Set environment variables interactively via echo pipe
env_vars = {
    'BACKEND_API_URL': 'http://18.213.66.136',
    'NEXT_PUBLIC_API_URL': 'http://18.213.66.136',
    'SBA_API_URL': 'http://18.213.66.136/api/sba',
}

for key, value in env_vars.items():
    print(f"Setting {key}={value}...")
    r = subprocess.run(
        f'echo {value} | npx vercel env add {key} production',
        shell=True, capture_output=True, text=True, timeout=30
    )
    out = r.stdout + r.stderr
    if 'added' in out.lower() or 'existing' in out.lower():
        print(f"  ✅ {key} set")
    else:
        print(f"  {out[:200]}")

print("\nDeploying frontend to Vercel...")
r = subprocess.run(
    'npx vercel --prod --yes',
    shell=True, capture_output=True, text=True, timeout=120
)
print(r.stdout[-500:])
if r.stderr:
    print(f"ERR: {r.stderr[:200]}")
