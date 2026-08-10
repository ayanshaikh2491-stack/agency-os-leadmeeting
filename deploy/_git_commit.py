import subprocess, os

os.chdir(r"C:\Users\TAUSHEF\Downloads\int")

def sh(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(">>>", cmd)
    print(r.stdout.strip()[:3000])
    if r.stderr.strip():
        print("ERR:", r.stderr.strip()[:800])
    return r

# Commit only the meaningful migration files (leave scratch _*.py untracked)
sh('git add STATE.md deploy/pb_gateway.py deploy/_pb_gw_test.py deploy/_pb_import.py deploy/sba-gateway.service deploy/deploy_sba.py deploy/_pb_init.py deploy/_pb_install_ec2.sh')
sh('git commit -m "feat(pocketbase): gateway GREEN on EC2 - id remap + pagination fix, autopilot on 8095, Supabase stopped"')
sh("git log --oneline -2")
