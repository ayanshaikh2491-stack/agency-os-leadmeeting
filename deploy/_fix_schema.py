import io

path = r'agency-frontend/supabase/schema.sql'
with io.open(path, encoding='utf-8') as f:
    text = f.read()

stub_rows = [
    "  ('00000000-0000-0000-0000-000000000001', 'intake-researcher', 'Intake Researcher', 'worker', '\U0001F50D', '#45aaf2', 'active', 'http://18.213.66.136:8000/api/agents/intake-researcher/chat'),\n",
    "  ('00000000-0000-0000-0000-000000000001', 'sales-closer', 'Sales Closer', 'worker', '\U0001F4BC', '#f368e0', 'active', 'http://18.213.66.136:8000/api/agents/sales-closer/chat'),\n",
    "  ('00000000-0000-0000-0000-000000000001', 'client-success', 'Client Success', 'worker', '\U0001F91D', '#26de81', 'active', 'http://18.213.66.136:8000/api/agents/client-success/chat'),\n",
    "  ('00000000-0000-0000-0000-000000000001', 'review-qc', 'Review & QC', 'worker', '\u2713', '#fd9644', 'active', 'http://18.213.66.136:8000/api/agents/review-qc/chat')\n",
]
removed = 0
for row in stub_rows:
    if row in text:
        text = text.replace(row, '')
        removed += 1

# Add website-builder + social-manager rows before the ON CONFLICT line of worker insert
add_rows = [
    "  ('00000000-0000-0000-0000-000000000001', 'website-builder', 'Website Agent', 'worker', '\U0001F310', '#26de81', 'active', 'http://18.213.66.136:8000/api/agents/website-builder/chat'),\n",
    "  ('00000000-0000-0000-0000-000000000001', 'social-manager', 'Social Manager', 'worker', '\U0001F4F1', '#45aaf2', 'active', 'http://18.213.66.136:8000/api/agents/social-manager/chat')\n",
]
# Append before the ON CONFLICT line that follows analytics-bot row
anchor = "'#a55eea', 'active', 'http://18.213.66.136:8000/api/agents/analytics-bot/chat'),\n"
insert_idx = text.find(anchor)
if insert_idx >= 0:
    end = insert_idx + len(anchor)
    text = text[:end] + ''.join(add_rows) + text[end:]
    added = True
else:
    added = False

with io.open(path, 'w', encoding='utf-8', newline='') as f:
    f.write(text)
print('removed rows:', removed, '| added rows:', added)
