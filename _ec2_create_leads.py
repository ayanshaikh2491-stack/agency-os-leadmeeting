import subprocess

KEY = r"C:\Users\TAUSHEF\Downloads\int\ec2-key.pem"
HOST = "ubuntu@18.213.66.136"

def ssh(cmd, timeout=120):
    full = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10",
            "-i", KEY, HOST, cmd]
    r = subprocess.run(full, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return r

# Create leads table
create_sql = """
CREATE TABLE IF NOT EXISTS leads (
  id BIGSERIAL PRIMARY KEY,
  client_id UUID DEFAULT '00000000-0000-0000-0000-000000000001' REFERENCES clients(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  has_website BOOLEAN DEFAULT false,
  phone TEXT,
  category TEXT,
  city_state TEXT,
  address TEXT,
  href TEXT,
  text TEXT,
  mode TEXT,
  website_status TEXT,
  status TEXT DEFAULT 'candidate' CHECK (status IN ('candidate','good','verified','contacted','closed')),
  raw JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_client ON leads(client_id);
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
"""
r = ssh("cat > /tmp/create_leads.sql << 'EOF'\n" + create_sql + "\nEOF\ndocker cp /tmp/create_leads.sql supabase-db:/tmp/ && docker exec supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=0 -f /tmp/create_leads.sql 2>&1 | tail -10")
print("=== CREATE LEADS TABLE ===")
print(r.stdout[:1500])
if r.stderr.strip():
    print("ERR:", r.stderr[-400:])
