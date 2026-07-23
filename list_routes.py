"""List SBA routes - handle encoding"""
import re
with open('admin/api/routes/sba.py', encoding='utf-8', errors='replace') as f:
    content = f.read()
routes = re.findall(r'@router\.(get|post|put|delete|patch)\("([^"]+)"\)', content)
for method, path in routes:
    print(f'  {method.upper():7s} {path}')
print(f'\nTotal: {len(routes)} endpoints')
