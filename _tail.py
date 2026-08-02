import sys

with open("maps_full_run.txt", encoding="utf-8", errors="replace") as f:
    lines = f.readlines()
print("".join(lines[-15:]))
