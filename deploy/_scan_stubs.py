"""Scan frontend + backend for remaining stub agent references."""
import io, os

stubs = ['intake-researcher', 'sales-closer', 'client-success', 'review-qc']
root = r'agency-frontend/src'
hits = []
for dirpath, dirnames, filenames in os.walk(root):
    for fn in filenames:
        if not (fn.endswith('.js') or fn.endswith('.jsx') or fn.endswith('.ts') or fn.endswith('.tsx')):
            continue
        p = os.path.join(dirpath, fn)
        try:
            text = io.open(p, encoding='utf-8').read()
        except Exception:
            continue
        for s in stubs:
            if s in text:
                hits.append((p, s))

print("STUB REFERENCES FOUND:", len(hits))
for p, s in hits:
    print(" ", p, '->', s)
