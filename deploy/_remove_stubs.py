"""Remove stub-agent lines from frontend files."""
import io

def strip_lines(path, needles):
    with io.open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    out = []
    removed = 0
    for ln in lines:
        if any(n in ln for n in needles):
            removed += 1
            continue
        out.append(ln)
    with io.open(path, 'w', encoding='utf-8', newline='') as f:
        f.writelines(out)
    print(path, 'removed', removed)

strip_lines(r'agency-frontend/src/components/agents/AgentList.jsx',
            ['intake-researcher', 'sales-closer', 'client-success', 'review-qc'])
strip_lines(r'agency-frontend/src/lib/client-context.js',
            ["'intake-researcher'", "'sales-closer'", "'client-success'", "'review-qc'"])
strip_lines(r'agency-frontend/src/lib/chat-utils.js',
            ["'sales-closer'", "'client-success'", "'review-qc'"])
