-- Migration 0001: pgvector extension and tool embeddings
-- Phase 2: Tool Catalog & Retrieval
-- Purpose: Enable semantic search for tool selection using pgvector

-- ============================================================================
-- 1. Enable pgvector extension
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- 2. Create tool_embeddings table
-- ============================================================================

CREATE TABLE IF NOT EXISTS tool_catalog.tool_embeddings (
    -- Primary key and foreign key to tools table
    tool_id INTEGER PRIMARY KEY REFERENCES tool_catalog.tools(id) ON DELETE CASCADE,
    
    -- Embedding vector (768d for most embedding models)
    embedding vector(768) NOT NULL,
    
    -- Metadata for tracking
    embedding_model VARCHAR(100) NOT NULL DEFAULT 'bge-base-en-v1.5',
    embedding_provider VARCHAR(50) NOT NULL DEFAULT 'openai',
    
    -- Tracking
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- 3. Create IVFFlat index for fast similarity search
-- ============================================================================

-- Create IVFFlat index with cosine distance
-- Lists parameter: sqrt(total_rows) is a good starting point
-- For ~100-1000 tools, lists=100 is reasonable
CREATE INDEX IF NOT EXISTS idx_tool_embeddings_ivfflat
    ON tool_catalog.tool_embeddings 
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- ============================================================================
-- 4. Create function to update updated_at timestamp
-- ============================================================================

CREATE OR REPLACE FUNCTION tool_catalog.update_tool_embeddings_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_tool_embeddings_updated_at
    BEFORE UPDATE ON tool_catalog.tool_embeddings
    FOR EACH ROW
    EXECUTE FUNCTION tool_catalog.update_tool_embeddings_updated_at();

-- ============================================================================
-- 5. Create helper view for tool retrieval
-- ============================================================================

CREATE OR REPLACE VIEW tool_catalog.tools_with_embeddings AS
SELECT 
    t.id,
    t.tool_name,
    t.description,
    t.platform,
    t.category,
    t.enabled,
    te.embedding,
    te.embedding_model,
    te.updated_at as embedding_updated_at
FROM tool_catalog.tools t
LEFT JOIN tool_catalog.tool_embeddings te ON t.id = te.tool_id
WHERE t.enabled = true AND t.is_latest = true;

-- ============================================================================
-- NOTES
-- ============================================================================

-- Embedding generation:
-- - Use environment variables for provider/model/key configuration
-- - Default: OpenAI text-embedding-3-small (768d)
-- - Alternative: bge-base-en-v1.5, sentence-transformers, etc.
-- - Embed: tool_name + description + platform + category

-- Similarity search:
-- - Use cosine distance operator: <=>
-- - Lower distance = higher similarity
-- - Typical query: ORDER BY embedding <=> query_embedding LIMIT k

-- Index maintenance:
-- - Run ANALYZE after bulk inserts: ANALYZE tool_catalog.tool_embeddings;
-- - Rebuild index if needed: REINDEX INDEX idx_tool_embeddings_ivfflat;