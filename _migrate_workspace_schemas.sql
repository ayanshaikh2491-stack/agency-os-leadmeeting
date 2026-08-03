-- ─────────────────────────────────────────────────────────────
-- Workspace-scoped, per-agent Supabase schema migration
--
-- Structure: each workspace owns a Postgres schema `ws_<slug>`,
-- and inside that schema each agent owns its own tables:
--   ws_agency.leads, ws_agency.clients            (SBA agent)
--   ws_agency.website_builds, ws_agency.website_docs,
--   ws_agency.website_build_log                   (Website agent)
--
-- New workspace => run: SELECT public.provision_workspace('Name');
-- (or POST /rest/v1/rpc/provision_workspace {"ws_name":"Name"})
--
-- Idempotent: safe to run repeatedly. Does NOT drop or alter any
-- existing public tables (legacy flat tables stay untouched).
-- ─────────────────────────────────────────────────────────────

-- 1. Workspaces registry
CREATE TABLE IF NOT EXISTS public.workspaces (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 2. Slug helper: 'My Workspace!' -> 'my_workspace'
CREATE OR REPLACE FUNCTION public.workspace_slug(name text)
RETURNS text AS $$
  SELECT COALESCE(
    NULLIF(
      regexp_replace(
        regexp_replace(lower(COALESCE(name, '')), '[^a-z0-9]+', '_', 'g'),
        '^[0-9_]+', '', 'g'),
      ''),
    'default');
$$ LANGUAGE sql IMMUTABLE;

-- 3. Provision a workspace: create ws_<slug> schema + all agent tables
CREATE OR REPLACE FUNCTION public.provision_workspace(ws_name text)
RETURNS text AS $$
DECLARE
  slug text := public.workspace_slug(ws_name);
  sch text := 'ws_' || slug;
BEGIN
  EXECUTE format('CREATE SCHEMA IF NOT EXISTS %I', sch);

  -- ── SBA agent tables ─────────────────────────────────────
  EXECUTE format($ddl$
    CREATE TABLE IF NOT EXISTS %I.leads (
      id BIGSERIAL PRIMARY KEY,
      name TEXT NOT NULL,
      has_website BOOLEAN DEFAULT FALSE,
      phone TEXT DEFAULT '',
      category TEXT DEFAULT '',
      city_state TEXT DEFAULT '',
      address TEXT DEFAULT '',
      href TEXT DEFAULT '',
      text TEXT DEFAULT '',
      mode TEXT DEFAULT 'card',
      website_status TEXT DEFAULT 'verified_none',
      status TEXT DEFAULT 'candidate',
      raw JSONB DEFAULT '{}'::jsonb,
      created_at TIMESTAMPTZ DEFAULT now(),
      updated_at TIMESTAMPTZ DEFAULT now()
    )$ddl$, sch);
  EXECUTE format($ddl$
    CREATE TABLE IF NOT EXISTS %I.clients (
      id BIGSERIAL PRIMARY KEY,
      name TEXT NOT NULL UNIQUE,
      email TEXT DEFAULT '',
      phone TEXT DEFAULT '',
      category TEXT DEFAULT '',
      city_state TEXT DEFAULT '',
      status TEXT DEFAULT 'active',
      created_at TIMESTAMPTZ DEFAULT now(),
      updated_at TIMESTAMPTZ DEFAULT now()
    )$ddl$, sch);

  -- ── Website agent tables ─────────────────────────────────
  EXECUTE format($ddl$
    CREATE TABLE IF NOT EXISTS %I.website_builds (
      id BIGSERIAL PRIMARY KEY,
      client_name TEXT NOT NULL DEFAULT 'Client',
      status TEXT NOT NULL DEFAULT 'draft',          -- draft|building|live|improving|failed
      current_stage TEXT NOT NULL DEFAULT '',
      site_url TEXT DEFAULT '',
      repo_url TEXT DEFAULT '',
      framework TEXT DEFAULT 'nextjs',
      created_at TIMESTAMPTZ DEFAULT now(),
      updated_at TIMESTAMPTZ DEFAULT now(),
      UNIQUE(client_name)
    )$ddl$, sch);
  EXECUTE format($ddl$
    CREATE TABLE IF NOT EXISTS %I.website_docs (
      id BIGSERIAL PRIMARY KEY,
      client_name TEXT NOT NULL DEFAULT 'Client',
      doc_type TEXT NOT NULL,   -- business_brief|site_requirements|brand_colors|design_system|content_plan|tech_deploy_plan
      title TEXT DEFAULT '',
      content TEXT DEFAULT '',
      version INT NOT NULL DEFAULT 1,
      created_at TIMESTAMPTZ DEFAULT now(),
      updated_at TIMESTAMPTZ DEFAULT now(),
      UNIQUE(client_name, doc_type)
    )$ddl$, sch);
  EXECUTE format($ddl$
    CREATE TABLE IF NOT EXISTS %I.website_build_log (
      id BIGSERIAL PRIMARY KEY,
      client_name TEXT NOT NULL DEFAULT 'Client',
      event_type TEXT NOT NULL,   -- chat|build_start|build_step|improve|deploy|error
      message TEXT DEFAULT '',
      actor TEXT DEFAULT 'website_agent',  -- user|website_agent|ceo|sba|seo
      created_at TIMESTAMPTZ DEFAULT now()
    )$ddl$, sch);

  -- ── Generic per-agent tables (any agent in this workspace) ──
  -- agent_memory: key/value memory per agent (what it learned, state, notes)
  EXECUTE format($ddl$
    CREATE TABLE IF NOT EXISTS %I.agent_memory (
      id BIGSERIAL PRIMARY KEY,
      agent_name TEXT NOT NULL DEFAULT 'agent',   -- sba|website|seo|social|content|ads|analytics
      memory_key TEXT NOT NULL,
      value JSONB DEFAULT '{}'::jsonb,
      created_at TIMESTAMPTZ DEFAULT now(),
      updated_at TIMESTAMPTZ DEFAULT now(),
      UNIQUE(agent_name, memory_key)
    )$ddl$, sch);
  -- agent_messages: per-agent chat history
  EXECUTE format($ddl$
    CREATE TABLE IF NOT EXISTS %I.agent_messages (
      id BIGSERIAL PRIMARY KEY,
      agent_name TEXT NOT NULL DEFAULT 'agent',
      role TEXT NOT NULL,          -- user|assistant|system|tool
      content TEXT DEFAULT '',
      meta JSONB DEFAULT '{}'::jsonb,
      created_at TIMESTAMPTZ DEFAULT now()
    )$ddl$, sch);
  -- agent_data: arbitrary per-agent documents/state (JSON)
  EXECUTE format($ddl$
    CREATE TABLE IF NOT EXISTS %I.agent_data (
      id BIGSERIAL PRIMARY KEY,
      agent_name TEXT NOT NULL DEFAULT 'agent',
      data_key TEXT NOT NULL,
      payload JSONB DEFAULT '{}'::jsonb,
      created_at TIMESTAMPTZ DEFAULT now(),
      updated_at TIMESTAMPTZ DEFAULT now(),
      UNIQUE(agent_name, data_key)
    )$ddl$, sch);
  -- agent_checkpoints: LangGraph memory (checkpoint per thread)
  EXECUTE format($ddl$
    CREATE TABLE IF NOT EXISTS %I.agent_checkpoints (
      agent_name TEXT NOT NULL DEFAULT 'agent',
      thread_id TEXT NOT NULL,
      checkpoint_id TEXT NOT NULL,
      checkpoint JSONB NOT NULL,
      metadata JSONB DEFAULT '{}'::jsonb,
      parent_checkpoint_id TEXT DEFAULT '',
      created_at TIMESTAMPTZ DEFAULT now(),
      PRIMARY KEY (agent_name, thread_id, checkpoint_id)
    )$ddl$, sch);
  -- agent_checkpoint_writes: pending writes per checkpoint task
  EXECUTE format($ddl$
    CREATE TABLE IF NOT EXISTS %I.agent_checkpoint_writes (
      agent_name TEXT NOT NULL DEFAULT 'agent',
      thread_id TEXT NOT NULL,
      checkpoint_id TEXT NOT NULL,
      task_id TEXT NOT NULL,
      writes JSONB DEFAULT '[]'::jsonb,
      created_at TIMESTAMPTZ DEFAULT now(),
      PRIMARY KEY (agent_name, thread_id, checkpoint_id, task_id)
    )$ddl$, sch);

  EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%s_website_builds ON %I.website_builds (client_name)', replace(sch, '.', '_'), sch);
  EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%s_website_docs ON %I.website_docs (client_name, doc_type)', replace(sch, '.', '_'), sch);
  EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%s_website_log ON %I.website_build_log (client_name, created_at DESC)', replace(sch, '.', '_'), sch);

  RETURN sch;
END;
$$ LANGUAGE plpgsql;

-- 4. Seed the registry with existing workspaces
INSERT INTO public.workspaces (name, description) VALUES
    ('agency', 'Agency default workspace — SBA pipeline'),
    ('Default', 'Fallback workspace')
ON CONFLICT (name) DO NOTHING;

-- 5. Provision schemas for every registered workspace
DO $$
DECLARE w record;
BEGIN
  FOR w IN SELECT name FROM public.workspaces LOOP
    PERFORM public.provision_workspace(w.name);
  END LOOP;
END $$;

-- 6. Copy legacy public.leads into ws_agency.leads (one-time, only if
--    the target is empty). Existing flat table is NOT dropped.
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.tables
             WHERE table_schema = 'public' AND table_name = 'leads')
     AND EXISTS (SELECT 1 FROM information_schema.tables
                 WHERE table_schema = 'ws_agency' AND table_name = 'leads')
     AND NOT EXISTS (SELECT 1 FROM ws_agency.leads LIMIT 1) THEN
    INSERT INTO ws_agency.leads
      (name, has_website, phone, category, city_state, address, href,
       text, mode, website_status, status, raw)
    SELECT name, has_website, phone, category, city_state, address, href,
           text, mode, website_status, status,
           CASE WHEN raw IS NULL THEN NULL ELSE raw::jsonb END
    FROM public.leads;
  END IF;
END $$;
