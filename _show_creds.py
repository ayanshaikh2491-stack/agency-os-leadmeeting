txt = open(r"C:\Users\TAUSHEF\Downloads\int\_supabase.env", encoding="utf-8").read()
for line in txt.splitlines():
    if "DASHBOARD" in line or "SUPABASE_PUBLIC_URL" in line or "API_EXTERNAL_URL" in line or "SITE_URL" in line:
        print(line)
