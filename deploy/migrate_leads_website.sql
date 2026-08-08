-- Leads table: add website column (applied 2026-08-08 to EC2 supabase-db)
-- Root cause: autopilot saves rows with a `website` key, but the Supabase
-- public.leads schema had no `website` column -> PostgREST 400 PGRST204
-- ("Could not find the 'website' column") on every new-lead insert, and the
-- FIX10 backfill patch could not store Maps card websites.
-- Additive and idempotent; safe to run on any environment.
--
-- Run: docker exec supabase-db psql -U postgres -d postgres -f deploy/migrate_leads_website.sql

ALTER TABLE public.leads ADD COLUMN IF NOT EXISTS website text;
