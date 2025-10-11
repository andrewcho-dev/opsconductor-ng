-- Migration: Add pgvector extension and tool_index table for semantic tool retrieval
-- Purpose: Enable Stage AB to use semantic search for tool selection instead of loading all tools
-- Date: 2025-01-XX
-- Confidence: 0.95 | Doubt: Managed PG may not allow HNSW; fallback to IVFFLAT

-- ============================================================================
-- 1. Enable pgvector extension
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- 2. Create tool_index table (compact index for semantic retrieval)
-- ============================================================================

CREATE TABLE IF NOT EXISTS tool_catalog.tool_index (
    -- Identity (matches tool_catalog.tools.tool_name)
    id TEXT PRIMARY KEY,
    
    -- Compact fields for LLM consumption (token-optimized)
    name TEXT NOT NULL,           -- Truncated to 48 chars max (append … if longer)
    desc_short TEXT NOT NULL,     -- Strict 110-char one-liner (truncate with …)
    platform TEXT NOT NULL,       -- windows | linux | both | cloud | network | multi-platform
    tags TEXT[] NOT NULL,         -- Max 6 tags; default ["misc"]
    cost_hint TEXT NOT NULL DEFAULT 'med', -- low | med | high (execution cost/risk)
    
    -- Embedding vector (768d for bge-base-en or 384d for bge-small-en)
    emb vector(768) NOT NULL,
    
    -- Tracking
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- 3. Create ANN index for fast similarity search
-- ============================================================================

-- Try HNSW first (best performance, requires pg 14+ and pgvector 0.5.0+)
-- If this fails, use IVFFLAT fallback below
DO $$
BEGIN
    -- Attempt to create HNSW index
    CREATE INDEX IF NOT EXISTS tool_index_emb_hnsw
        ON tool_catalog.tool_index USING hnsw (emb vector_cosine_ops);
    
    RAISE NOTICE 'Created HNSW index successfully';
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'HNSW not available, will use IVFFLAT fallback';
END $$;

-- Fallback: IVFFLAT index (if HNSW creation failed)
-- Uncomment and run manually if HNSW is not available:
-- CREATE INDEX IF NOT EXISTS tool_index_emb_ivf
--     ON tool_catalog.tool_index USING ivfflat (emb vector_cosine_ops) WITH (lists = 128);
-- ANALYZE tool_catalog.tool_index;

-- ============================================================================
-- 4. Create indexes for keyword/tag fallback search
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_tool_index_name ON tool_catalog.tool_index(name);
CREATE INDEX IF NOT EXISTS idx_tool_index_platform ON tool_catalog.tool_index(platform);
CREATE INDEX IF NOT EXISTS idx_tool_index_tags ON tool_catalog.tool_index USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_tool_index_updated_at ON tool_catalog.tool_index(updated_at);

-- ============================================================================
-- 5. Create function to update updated_at timestamp
-- ============================================================================

CREATE OR REPLACE FUNCTION tool_catalog.update_tool_index_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_tool_index_updated_at
    BEFORE UPDATE ON tool_catalog.tool_index
    FOR EACH ROW
    EXECUTE FUNCTION tool_catalog.update_tool_index_updated_at();

-- ============================================================================
-- 6. Create telemetry table for Stage AB monitoring
-- ============================================================================

CREATE TABLE IF NOT EXISTS tool_catalog.stage_ab_telemetry (
    id SERIAL PRIMARY KEY,
    
    -- Request context
    request_id TEXT NOT NULL,
    user_intent TEXT NOT NULL,
    
    -- Catalog metrics
    catalog_size INTEGER NOT NULL,
    candidates_before_budget INTEGER NOT NULL,
    rows_sent INTEGER NOT NULL,
    budget_used INTEGER NOT NULL,
    headroom_left INTEGER NOT NULL,
    
    -- Recall metrics
    selected_tool_ids TEXT[] NOT NULL,
    executed_tool_ids TEXT[],
    recall_at_k FLOAT, -- Was the executed tool in AB candidates?
    
    -- Truncation tracking
    truncation_events INTEGER DEFAULT 0,
    
    -- Performance
    retrieval_time_ms INTEGER,
    llm_time_ms INTEGER,
    total_time_ms INTEGER,
    
    -- Tracking
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_stage_ab_telemetry_request_id ON tool_catalog.stage_ab_telemetry(request_id);
CREATE INDEX idx_stage_ab_telemetry_created_at ON tool_catalog.stage_ab_telemetry(created_at);
CREATE INDEX idx_stage_ab_telemetry_recall ON tool_catalog.stage_ab_telemetry(recall_at_k);

-- ============================================================================
-- 7. Create view for monitoring alerts
-- ============================================================================

CREATE OR REPLACE VIEW tool_catalog.stage_ab_alerts AS
SELECT 
    id,
    request_id,
    user_intent,
    headroom_left,
    recall_at_k,
    truncation_events,
    created_at
FROM tool_catalog.stage_ab_telemetry
WHERE 
    headroom_left < 15 -- Less than 15% headroom
    OR recall_at_k < 0.98 -- Recall below threshold
    OR truncation_events > 0 -- Any truncation
ORDER BY created_at DESC;

-- ============================================================================
-- NOTES
-- ============================================================================

-- Embedding generation:
-- - Use bge-base-en (768d) or bge-small-en (384d)
-- - Embed: "{name} | {desc_short} | {tags_csv} | {platform}"
-- - Use cosine similarity for retrieval

-- Token budgeting (adjust as needed):
-- - CTX = 8192 (vLLM context)
-- - HEADROOM = 0.30 (30% for output)
-- - BASE_TOKENS = 900 (system + instructions + user text)
-- - TOKENS_PER_ROW_EST = 45 (~4 chars/token)
-- - budget = CTX - (CTX * HEADROOM) - BASE_TOKENS
-- - max_rows = max(10, floor(budget / TOKENS_PER_ROW_EST))

-- Recall pipeline:
-- 1. Vector Top-K: K=120 by cosine similarity (filtered by platform)
-- 2. Keyword/Tag Top-K: K=60 using ILIKE on name/desc_short
-- 3. Always-include IDs: ["asset-query", ...]
-- 4. Recently used: K=20 by recency log (optional)
-- 5. Union → de-dup → slice to max_rows

-- Confidence: 0.95
-- Doubt: Token estimates ±10-15%; keep 10% extra safety margin