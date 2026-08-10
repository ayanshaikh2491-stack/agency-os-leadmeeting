"""Remote DB counts for SBA pipeline."""
import os
try:
    from dotenv import load_dotenv; load_dotenv()
except Exception:
    pass
from supabase import create_client
u = os.getenv('SUPABASE_URL', 'http://localhost:8050').rstrip('/')
k = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
if not k:
    print('NO SUPABASE KEY')
    raise SystemExit
sb = create_client(u, k)
for tbl, col in [('leads', 'email'), ('leads', 'website'), ('leads', None)]:
    try:
        if col:
            r = sb.table(tbl).select('count').eq(col, '').execute()
            print(f'{tbl} with {col}=\'\':', r.data[0]['count'])
        else:
            r = sb.table(tbl).select('count').execute()
            print(f'{tbl} total:', r.data[0]['count'])
    except Exception as e:
        print(f'{tbl}/{col} ERR:', str(e)[:150])
for tbl in ['meetings', 'email_sends']:
    try:
        r = sb.table(tbl).select('count').execute()
        print(f'{tbl} total:', r.data[0]['count'])
    except Exception as e:
        print(f'{tbl} ERR:', str(e)[:150])
