lines = open(r"deploy\deploy_sba.py", encoding="utf-8").read().splitlines()
for i in range(36, 48):
    if i < len(lines):
        l = lines[i]
        print(f"[{i+1}] len={len(l)} repr={l!r}")
