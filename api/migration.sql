-- Supabase Migration: Create inquiries table
-- Run this in Supabase SQL Editor: https://app.supabase.com → SQL Editor

CREATE TABLE IF NOT EXISTS inquiries (
  id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name          TEXT NOT NULL,
  email         TEXT NOT NULL,
  travel_date   TEXT NOT NULL,
  travelers     INTEGER NOT NULL,
  tour_type     TEXT,
  budget        TEXT,
  message       TEXT,
  source        TEXT DEFAULT 'Website',
  status        TEXT DEFAULT 'new',
  lang          TEXT DEFAULT 'unknown',
  created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- Index for email lookups (dedup check)
CREATE INDEX IF NOT EXISTS idx_inquiries_email ON inquiries(email);

-- Index for sorting by date
CREATE INDEX IF NOT EXISTS idx_inquiries_created_at ON inquiries(created_at DESC);

-- Enable Row Level Security (RLS)
ALTER TABLE inquiries ENABLE ROW LEVEL SECURITY;

-- Allow inserts from anyone (the API uses service_role key, bypasses RLS)
-- But keep this policy for future use with anon key
CREATE POLICY "Allow inserts for all" ON inquiries
  FOR INSERT WITH CHECK (true);
