-- Ensure pgvector exists
CREATE EXTENSION IF NOT EXISTS vector;

-- Convert tags/platform to text[] if needed, or add if missing
DO $$
BEGIN
  -- tags -> text[]
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name='tool' AND column_name='tags' AND data_type='text'
  ) THEN
    ALTER TABLE tool
      ALTER COLUMN tags TYPE text[] USING CASE
        WHEN tags IS NULL THEN '{}'::text[] ELSE ARRAY[tags]
      END;
  ELSIF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name='tool' AND column_name='tags'
  ) THEN
    ALTER TABLE tool ADD COLUMN tags text[] DEFAULT '{}'::text[];
  END IF;

  -- platform -> text[]
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name='tool' AND column_name='platform' AND data_type='text'
  ) THEN
    ALTER TABLE tool
      ALTER COLUMN platform TYPE text[] USING CASE
        WHEN platform IS NULL THEN '{}'::text[] ELSE ARRAY[platform]
      END;
  ELSIF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name='tool' AND column_name='platform'
  ) THEN
    ALTER TABLE tool ADD COLUMN platform text[] DEFAULT '{}'::text[];
  END IF;
END $$;

-- Ensure defaults on array columns
ALTER TABLE tool ALTER COLUMN tags SET DEFAULT '{}'::text[];
ALTER TABLE tool ALTER COLUMN platform SET DEFAULT '{}'::text[];

-- Ensure other required columns exist
ALTER TABLE tool ADD COLUMN IF NOT EXISTS meta         jsonb        DEFAULT '{}'::jsonb;
ALTER TABLE tool ADD COLUMN IF NOT EXISTS usage_count  integer      DEFAULT 0;
ALTER TABLE tool ADD COLUMN IF NOT EXISTS updated_at   timestamptz  DEFAULT now();

-- Ensure embedding column exists (vector(128))
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name='tool' AND column_name='embedding'
  ) THEN
    ALTER TABLE tool ADD COLUMN embedding vector(128);
  END IF;
END $$;

-- Create missing indexes (no-ops if present)
CREATE INDEX IF NOT EXISTS tool_key_idx         ON tool(key);
CREATE INDEX IF NOT EXISTS tool_tags_gin        ON tool USING gin (tags);
CREATE INDEX IF NOT EXISTS tool_platform_gin    ON tool USING gin (platform);
CREATE INDEX IF NOT EXISTS tool_updated_at_idx  ON tool (updated_at);
CREATE INDEX IF NOT EXISTS tool_embed_ivff      ON tool USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);