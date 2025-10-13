-- Audit AI Queries Table
-- This table stores AI request/response traces for compliance and observability

CREATE TABLE IF NOT EXISTS audit_ai_queries (
    id BIGSERIAL PRIMARY KEY,
    trace_id VARCHAR(32) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    input TEXT NOT NULL,
    output TEXT NOT NULL,
    tools JSONB DEFAULT '[]'::jsonb,
    duration_ms INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    inserted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_audit_ai_queries_trace_id ON audit_ai_queries(trace_id);
CREATE INDEX IF NOT EXISTS idx_audit_ai_queries_user_id ON audit_ai_queries(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_ai_queries_created_at ON audit_ai_queries(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_ai_queries_inserted_at ON audit_ai_queries(inserted_at DESC);

-- GIN index for JSONB tools column (for querying tool executions)
CREATE INDEX IF NOT EXISTS idx_audit_ai_queries_tools ON audit_ai_queries USING GIN(tools);

-- Comments
COMMENT ON TABLE audit_ai_queries IS 'Audit trail for AI query/response interactions';
COMMENT ON COLUMN audit_ai_queries.trace_id IS 'W3C distributed trace ID';
COMMENT ON COLUMN audit_ai_queries.user_id IS 'User or service account identifier';
COMMENT ON COLUMN audit_ai_queries.input IS 'User input/prompt';
COMMENT ON COLUMN audit_ai_queries.output IS 'AI-generated response';
COMMENT ON COLUMN audit_ai_queries.tools IS 'JSONB array of tool executions: [{"name": "...", "latency_ms": 123, "ok": true}]';
COMMENT ON COLUMN audit_ai_queries.duration_ms IS 'Total query duration in milliseconds';
COMMENT ON COLUMN audit_ai_queries.created_at IS 'Timestamp when the query occurred';
COMMENT ON COLUMN audit_ai_queries.inserted_at IS 'Timestamp when the record was inserted into the database';