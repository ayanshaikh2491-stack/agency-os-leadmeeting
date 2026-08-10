"""Scan backend admin/ for remaining stub agent references."""
import io, os

stubs = ['intake-researcher', 'sales-closer', 'client-success', 'review-qc']
hits = []
for dirpath, dirnames, filenames in os.walk(r'admin'):
    for fn in filenames:
        if not fn.endswith('.py'):
            continue
        p = os.path.join(dirpath, fn)
        try:
            text = io.open(p, encoding='utf-8', errors='ignore').read()
        except Exception:
            continue
        for s in stubs:
            if s in text:
                hits.append((p, s))

print("BACKEND STUB REFERENCES:", len(hits))
for p, s in hits:
    print(" ", p, '->', s)
