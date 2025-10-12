-- Migration: Tool schema with pgvector support
-- Idempotent: safe to run multiple times

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create tool table
CREATE TABLE IF NOT EXISTS tool (
  id BIGSERIAL PRIMARY KEY,
  key TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  short_desc TEXT NOT NULL,
  platform TEXT[] DEFAULT '{}'::TEXT[],
  tags TEXT[] DEFAULT '{}'::TEXT[],
  meta JSONB DEFAULT '{}'::JSONB,
  embedding VECTOR(128),
  usage_count INTEGER DEFAULT 0,
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS tool_key_idx ON tool(key);
CREATE INDEX IF NOT EXISTS tool_tags_gin ON tool USING gin (tags);
CREATE INDEX IF NOT EXISTS tool_platform_gin ON tool USING gin (platform);
CREATE INDEX IF NOT EXISTS tool_updated_at_idx ON tool (updated_at);
CREATE INDEX IF NOT EXISTS tool_embed_ivff ON tool USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);