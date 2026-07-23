"""Try importing admin.main to check for errors"""
import sys
sys.path.insert(0, '.')
try:
    from admin.main import app
    print('Import OK')
except Exception as e:
    print(f'Import Error: {e}')
