with open('C:/Users/TAUSHEF/Downloads/int/admin/agency/sba.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    stripped = line.strip()
    if 'class SBAAgent' in stripped or 'def __init__' in stripped:
        print(f'Line {i+1}: {line.rstrip()}')
    if 'self.api_key' in stripped or 'self.model' in stripped or 'self.api_base' in stripped:
        print(f'Line {i+1}: {line.rstrip()}')
