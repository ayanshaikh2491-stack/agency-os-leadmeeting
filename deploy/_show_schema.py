import io
lines = io.open(r'agency-frontend/supabase/schema.sql', encoding='utf-8').readlines()
for i in range(256, 267):
    print(i + 1, repr(lines[i]))
