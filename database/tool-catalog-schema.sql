-- ============================================================================
-- TOOL CATALOG SCHEMA
-- Database-backed tool management system for 200+ tools
-- ============================================================================

-- Create schema
CREATE SCHEMA IF NOT EXISTS tool_catalog;

-- ============================================================================
-- 1. TOOLS - Main tool registry
-- ============================================================================

CREATE TABLE IF NOT EXISTS tool_catalog.tools (
    -- Identity
    id SERIAL PRIMARY KEY,
    tool_name VARCHAR(100) NOT NULL,
    version VARCHAR(20) NOT NULL,
    
    -- Basic Info
    description TEXT NOT NULL,
    platform VARCHAR(50) NOT NULL, -- linux, windows, network, scheduler, custom
    category VARCHAR(50) NOT NULL, -- system, network, automation, monitoring, security
    
    -- Status
    status VARCHAR(20) DEFAULT 'active', -- active, deprecated, disabled, testing
    enabled BOOLEAN DEFAULT true,
    
    -- Defaults (JSONB for flexibility)
    defaults JSONB NOT NULL DEFAULT '{}',
    -- Example: {"accuracy_level": "real-time", "freshness": "live", "data_source": "direct"}
    
    -- Dependencies
    dependencies JSONB DEFAULT '[]',
    -- Example: [{"name": "docker_daemon", "type": "service", "required": true}]
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    -- Example: {"author": "...", "tags": [...], "documentation_url": "..."}
    
    -- Versioning
    parent_version_id INTEGER REFERENCES tool_catalog.tools(id),
    is_latest BOOLEAN DEFAULT true,
    
    -- Tracking
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_by VARCHAR(100),
    
    -- Constraints
    UNIQUE(tool_name, version),
    CHECK (platform IN ('linux', 'windows', 'network', 'scheduler', 'custom', 'multi-platform')),
    CHECK (category IN ('system', 'network', 'automation', 'monitoring', 'security', 'database', 'cloud', 'container')),
    CHECK (status IN ('active', 'deprecated', 'disabled', 'testing', 'draft'))
);

-- Indexes for performance
CREATE INDEX idx_tools_name ON tool_catalog.tools(tool_name);
CREATE INDEX idx_tools_platform ON tool_catalog.tools(platform);
CREATE INDEX idx_tools_category ON tool_catalog.tools(category);
CREATE INDEX idx_tools_status ON tool_catalog.tools(status);
CREATE INDEX idx_tools_enabled ON tool_catalog.tools(enabled);
CREATE INDEX idx_tools_is_latest ON tool_catalog.tools(is_latest);
CREATE INDEX idx_tools_metadata ON tool_catalog.tools USING GIN (metadata);
CREATE INDEX idx_tools_created_at ON tool_catalog.tools(created_at);

-- Trigger to update updated_at
CREATE OR REPLACE FUNCTION tool_catalog.update_tools_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_tools_updated_at
    BEFORE UPDATE ON tool_catalog.tools
    FOR EACH ROW
    EXECUTE FUNCTION tool_catalog.update_tools_updated_at();

-- ============================================================================
-- 2. TOOL_CAPABILITIES - Tool capabilities
-- ============================================================================

CREATE TABLE IF NOT EXISTS tool_catalog.tool_capabilities (
    id SERIAL PRIMARY KEY,
    tool_id INTEGER NOT NULL REFERENCES tool_catalog.tools(id) ON DELETE CASCADE,
    
    -- Capability Info
    capability_name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    
    -- Tracking
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(tool_id, capability_name)
);

CREATE INDEX idx_capabilities_tool_id ON tool_catalog.tool_capabilities(tool_id);
CREATE INDEX idx_capabilities_name ON tool_catalog.tool_capabilities(capability_name);

-- ============================================================================
-- 3. TOOL_PATTERNS - Usage patterns for capabilities
-- ============================================================================

CREATE TABLE IF NOT EXISTS tool_catalog.tool_patterns (
    id SERIAL PRIMARY KEY,
    capability_id INTEGER NOT NULL REFERENCES tool_catalog.tool_capabilities(id) ON DELETE CASCADE,
    
    -- Pattern Info
    pattern_name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    
    -- Use Cases
    typical_use_cases JSONB DEFAULT '[]',
    -- Example: ["restart service", "reload configuration"]
    
    -- Performance Metrics (expressions as strings)
    time_estimate_ms VARCHAR(500) NOT NULL, -- Expression: "2000 + 0.5 * N"
    cost_estimate VARCHAR(500) NOT NULL,    -- Expression: "ceil(N / 100)"
    complexity_score DECIMAL(3,2) NOT NULL CHECK (complexity_score >= 0 AND complexity_score <= 1),
    
    -- Quality Metrics
    scope VARCHAR(50) NOT NULL,
    completeness VARCHAR(50) NOT NULL,
    
    -- Limitations
    limitations JSONB DEFAULT '[]',
    
    -- Policy Constraints
    policy JSONB NOT NULL,
    -- Example: {"max_cost": 10, "requires_approval": true, "production_safe": true}
    
    -- Preference Matching
    preference_match JSONB NOT NULL,
    -- Example: {"speed": 0.9, "accuracy": 1.0, "cost": 0.8, "complexity": 0.7, "completeness": 1.0}
    
    -- Input/Output Schemas
    required_inputs JSONB DEFAULT '[]',
    optional_inputs JSONB DEFAULT '[]',
    output_schema JSONB DEFAULT '{}',
    
    -- Examples
    examples JSONB DEFAULT '[]',
    
    -- Tracking
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(capability_id, pattern_name)
);

CREATE INDEX idx_patterns_capability_id ON tool_catalog.tool_patterns(capability_id);
CREATE INDEX idx_patterns_name ON tool_catalog.tool_patterns(pattern_name);
CREATE INDEX idx_patterns_use_cases ON tool_catalog.tool_patterns USING GIN (typical_use_cases);
CREATE INDEX idx_patterns_policy ON tool_catalog.tool_patterns USING GIN (policy);
CREATE INDEX idx_patterns_preference_match ON tool_catalog.tool_patterns USING GIN (preference_match);

-- Trigger to update updated_at
CREATE TRIGGER trigger_patterns_updated_at
    BEFORE UPDATE ON tool_catalog.tool_patterns
    FOR EACH ROW
    EXECUTE FUNCTION tool_catalog.update_tools_updated_at();

-- ============================================================================
-- 4. TOOL_TELEMETRY - Performance tracking
-- ============================================================================

CREATE TABLE IF NOT EXISTS tool_catalog.tool_telemetry (
    id SERIAL PRIMARY KEY,
    
    -- Tool Reference
    tool_id INTEGER NOT NULL REFERENCES tool_catalog.tools(id),
    capability_id INTEGER REFERENCES tool_catalog.tool_capabilities(id),
    pattern_id INTEGER REFERENCES tool_catalog.tool_patterns(id),
    
    -- Execution Context
    execution_id VARCHAR(100), -- Link to execution record
    user_id VARCHAR(100),
    environment VARCHAR(50), -- production, staging, development
    
    -- Performance Metrics
    actual_time_ms INTEGER NOT NULL,
    actual_cost DECIMAL(10,2),
    success BOOLEAN NOT NULL,
    error_message TEXT,
    error_type VARCHAR(100),
    
    -- Context Variables (for analysis)
    context_variables JSONB DEFAULT '{}',
    -- Example: {"N": 100, "file_size_kb": 5000}
    
    -- Estimated vs Actual
    estimated_time_ms INTEGER,
    estimated_cost DECIMAL(10,2),
    time_variance_percent DECIMAL(5,2), -- (actual - estimated) / estimated * 100
    cost_variance_percent DECIMAL(5,2),
    
    -- Tracking
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_telemetry_tool_id ON tool_catalog.tool_telemetry(tool_id);
CREATE INDEX idx_telemetry_pattern_id ON tool_catalog.tool_telemetry(pattern_id);
CREATE INDEX idx_telemetry_executed_at ON tool_catalog.tool_telemetry(executed_at);
CREATE INDEX idx_telemetry_success ON tool_catalog.tool_telemetry(success);
CREATE INDEX idx_telemetry_environment ON tool_catalog.tool_telemetry(environment);
CREATE INDEX idx_telemetry_user_id ON tool_catalog.tool_telemetry(user_id);
CREATE INDEX idx_telemetry_execution_id ON tool_catalog.tool_telemetry(execution_id);

-- Partitioning by month for performance (optional, for high-volume systems)
-- CREATE TABLE tool_catalog.tool_telemetry_2025_01 PARTITION OF tool_catalog.tool_telemetry
--     FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

-- ============================================================================
-- 5. TOOL_AB_TESTS - A/B testing for optimization
-- ============================================================================

CREATE TABLE IF NOT EXISTS tool_catalog.tool_ab_tests (
    id SERIAL PRIMARY KEY,
    
    -- Test Info
    test_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    hypothesis TEXT, -- What are we testing?
    
    -- Tool Versions Being Tested
    tool_a_id INTEGER NOT NULL REFERENCES tool_catalog.tools(id),
    tool_b_id INTEGER NOT NULL REFERENCES tool_catalog.tools(id),
    
    -- Test Configuration
    traffic_split DECIMAL(3,2) DEFAULT 0.5 CHECK (traffic_split >= 0 AND traffic_split <= 1),
    target_environment VARCHAR(50), -- production, staging, etc.
    target_users JSONB DEFAULT '[]', -- Specific users or groups
    target_criteria JSONB DEFAULT '{}', -- Additional targeting criteria
    
    -- Test Metrics
    success_metric VARCHAR(100), -- What defines success? (time, cost, success_rate, etc.)
    minimum_sample_size INTEGER DEFAULT 100,
    confidence_level DECIMAL(3,2) DEFAULT 0.95,
    
    -- Test Status
    status VARCHAR(20) DEFAULT 'draft', -- draft, active, completed, cancelled
    
    -- Results
    tool_a_executions INTEGER DEFAULT 0,
    tool_b_executions INTEGER DEFAULT 0,
    tool_a_avg_time_ms DECIMAL(10,2),
    tool_b_avg_time_ms DECIMAL(10,2),
    tool_a_success_rate DECIMAL(5,4),
    tool_b_success_rate DECIMAL(5,4),
    
    winner_tool_id INTEGER REFERENCES tool_catalog.tools(id),
    statistical_significance DECIMAL(5,4), -- p-value
    results JSONB DEFAULT '{}',
    conclusion TEXT,
    
    -- Tracking
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    
    CHECK (tool_a_id != tool_b_id),
    CHECK (status IN ('draft', 'active', 'completed', 'cancelled'))
);

CREATE INDEX idx_ab_tests_status ON tool_catalog.tool_ab_tests(status);
CREATE INDEX idx_ab_tests_started_at ON tool_catalog.tool_ab_tests(started_at);
CREATE INDEX idx_ab_tests_tool_a_id ON tool_catalog.tool_ab_tests(tool_a_id);
CREATE INDEX idx_ab_tests_tool_b_id ON tool_catalog.tool_ab_tests(tool_b_id);

-- ============================================================================
-- 6. TOOL_AUDIT_LOG - Change tracking
-- ============================================================================

CREATE TABLE IF NOT EXISTS tool_catalog.tool_audit_log (
    id SERIAL PRIMARY KEY,
    
    -- What Changed
    tool_id INTEGER REFERENCES tool_catalog.tools(id),
    entity_type VARCHAR(50) NOT NULL, -- tool, capability, pattern
    entity_id INTEGER NOT NULL,
    action VARCHAR(50) NOT NULL, -- created, updated, deleted, enabled, disabled, deprecated
    
    -- Change Details
    changes JSONB NOT NULL,
    -- Example: {"field": "time_estimate_ms", "old_value": "1000", "new_value": "1200"}
    
    -- Who and When
    changed_by VARCHAR(100) NOT NULL,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Context
    reason TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    
    CHECK (entity_type IN ('tool', 'capability', 'pattern', 'ab_test')),
    CHECK (action IN ('created', 'updated', 'deleted', 'enabled', 'disabled', 'deprecated', 'activated', 'completed'))
);

CREATE INDEX idx_audit_tool_id ON tool_catalog.tool_audit_log(tool_id);
CREATE INDEX idx_audit_entity_type ON tool_catalog.tool_audit_log(entity_type);
CREATE INDEX idx_audit_entity_id ON tool_catalog.tool_audit_log(entity_id);
CREATE INDEX idx_audit_action ON tool_catalog.tool_audit_log(action);
CREATE INDEX idx_audit_changed_at ON tool_catalog.tool_audit_log(changed_at);
CREATE INDEX idx_audit_changed_by ON tool_catalog.tool_audit_log(changed_by);

-- ============================================================================
-- 7. TOOL_CACHE - Performance cache for frequently accessed tools
-- ============================================================================

CREATE TABLE IF NOT EXISTS tool_catalog.tool_cache (
    id SERIAL PRIMARY KEY,
    
    -- Cache Key
    cache_key VARCHAR(255) NOT NULL UNIQUE,
    
    -- Cached Data
    tool_data JSONB NOT NULL,
    
    -- Cache Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    hit_count INTEGER DEFAULT 0,
    last_accessed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_cache_key ON tool_catalog.tool_cache(cache_key);
CREATE INDEX idx_cache_expires_at ON tool_catalog.tool_cache(expires_at);

-- ============================================================================
-- VIEWS - Convenient access patterns
-- ============================================================================

-- View: Latest version of each tool
CREATE OR REPLACE VIEW tool_catalog.v_latest_tools AS
SELECT 
    t.*,
    COUNT(DISTINCT tc.id) as capability_count,
    COUNT(DISTINCT tp.id) as pattern_count
FROM tool_catalog.tools t
LEFT JOIN tool_catalog.tool_capabilities tc ON t.id = tc.tool_id
LEFT JOIN tool_catalog.tool_patterns tp ON tc.id = tp.capability_id
WHERE t.is_latest = true AND t.enabled = true
GROUP BY t.id;

-- View: Tool performance summary
CREATE OR REPLACE VIEW tool_catalog.v_tool_performance AS
SELECT 
    t.id as tool_id,
    t.tool_name,
    t.version,
    COUNT(tel.id) as execution_count,
    AVG(tel.actual_time_ms) as avg_time_ms,
    AVG(tel.actual_cost) as avg_cost,
    SUM(CASE WHEN tel.success THEN 1 ELSE 0 END)::FLOAT / COUNT(tel.id) as success_rate,
    AVG(tel.time_variance_percent) as avg_time_variance_percent,
    AVG(tel.cost_variance_percent) as avg_cost_variance_percent
FROM tool_catalog.tools t
LEFT JOIN tool_catalog.tool_telemetry tel ON t.id = tel.tool_id
WHERE tel.executed_at > CURRENT_TIMESTAMP - INTERVAL '30 days'
GROUP BY t.id, t.tool_name, t.version;

-- View: Tool catalog summary
CREATE OR REPLACE VIEW tool_catalog.v_catalog_summary AS
SELECT 
    platform,
    category,
    status,
    COUNT(*) as tool_count,
    COUNT(DISTINCT tool_name) as unique_tools,
    SUM(CASE WHEN is_latest THEN 1 ELSE 0 END) as latest_versions
FROM tool_catalog.tools
GROUP BY platform, category, status;

-- ============================================================================
-- FUNCTIONS - Helper functions
-- ============================================================================

-- Function: Get tool by name (latest version)
CREATE OR REPLACE FUNCTION tool_catalog.get_tool_by_name(p_tool_name VARCHAR)
RETURNS TABLE (
    tool_id INTEGER,
    tool_name VARCHAR,
    version VARCHAR,
    description TEXT,
    platform VARCHAR,
    category VARCHAR,
    capabilities JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.id,
        t.tool_name,
        t.version,
        t.description,
        t.platform,
        t.category,
        jsonb_agg(
            jsonb_build_object(
                'capability_name', tc.capability_name,
                'description', tc.description
            )
        ) as capabilities
    FROM tool_catalog.tools t
    LEFT JOIN tool_catalog.tool_capabilities tc ON t.id = tc.tool_id
    WHERE t.tool_name = p_tool_name 
      AND t.is_latest = true 
      AND t.enabled = true
    GROUP BY t.id, t.tool_name, t.version, t.description, t.platform, t.category;
END;
$$ LANGUAGE plpgsql;

-- Function: Search tools by capability
CREATE OR REPLACE FUNCTION tool_catalog.search_by_capability(p_capability_name VARCHAR)
RETURNS TABLE (
    tool_id INTEGER,
    tool_name VARCHAR,
    version VARCHAR,
    capability_name VARCHAR,
    pattern_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.id,
        t.tool_name,
        t.version,
        tc.capability_name,
        COUNT(tp.id) as pattern_count
    FROM tool_catalog.tools t
    JOIN tool_catalog.tool_capabilities tc ON t.id = tc.tool_id
    LEFT JOIN tool_catalog.tool_patterns tp ON tc.id = tp.capability_id
    WHERE tc.capability_name = p_capability_name
      AND t.is_latest = true
      AND t.enabled = true
    GROUP BY t.id, t.tool_name, t.version, tc.capability_name;
END;
$$ LANGUAGE plpgsql;

-- Function: Record telemetry
CREATE OR REPLACE FUNCTION tool_catalog.record_telemetry(
    p_tool_id INTEGER,
    p_pattern_id INTEGER,
    p_actual_time_ms INTEGER,
    p_actual_cost DECIMAL,
    p_success BOOLEAN,
    p_context_variables JSONB,
    p_execution_id VARCHAR DEFAULT NULL,
    p_user_id VARCHAR DEFAULT NULL,
    p_environment VARCHAR DEFAULT 'production'
) RETURNS INTEGER AS $$
DECLARE
    v_telemetry_id INTEGER;
BEGIN
    INSERT INTO tool_catalog.tool_telemetry (
        tool_id,
        pattern_id,
        actual_time_ms,
        actual_cost,
        success,
        context_variables,
        execution_id,
        user_id,
        environment
    ) VALUES (
        p_tool_id,
        p_pattern_id,
        p_actual_time_ms,
        p_actual_cost,
        p_success,
        p_context_variables,
        p_execution_id,
        p_user_id,
        p_environment
    ) RETURNING id INTO v_telemetry_id;
    
    RETURN v_telemetry_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- INITIAL DATA - Bootstrap with existing tools
-- ============================================================================

-- This will be populated by the migration script from YAML files

-- ============================================================================
-- PERMISSIONS
-- ============================================================================

-- Grant permissions to opsconductor user
GRANT USAGE ON SCHEMA tool_catalog TO opsconductor;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA tool_catalog TO opsconductor;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA tool_catalog TO opsconductor;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA tool_catalog TO opsconductor;

-- ============================================================================
-- COMMENTS - Documentation
-- ============================================================================

COMMENT ON SCHEMA tool_catalog IS 'Tool catalog system for managing 200+ operational tools';
COMMENT ON TABLE tool_catalog.tools IS 'Main tool registry with versioning support';
COMMENT ON TABLE tool_catalog.tool_capabilities IS 'Capabilities provided by each tool';
COMMENT ON TABLE tool_catalog.tool_patterns IS 'Usage patterns for each capability with performance profiles';
COMMENT ON TABLE tool_catalog.tool_telemetry IS 'Performance telemetry for actual tool executions';
COMMENT ON TABLE tool_catalog.tool_ab_tests IS 'A/B testing framework for tool optimization';
COMMENT ON TABLE tool_catalog.tool_audit_log IS 'Audit trail for all tool catalog changes';
COMMENT ON TABLE tool_catalog.tool_cache IS 'Performance cache for frequently accessed tools';

-- ============================================================================
-- MAINTENANCE
-- ============================================================================

-- Cleanup old telemetry data (keep last 90 days)
CREATE OR REPLACE FUNCTION tool_catalog.cleanup_old_telemetry()
RETURNS INTEGER AS $$
DECLARE
    v_deleted_count INTEGER;
BEGIN
    DELETE FROM tool_catalog.tool_telemetry
    WHERE executed_at < CURRENT_TIMESTAMP - INTERVAL '90 days';
    
    GET DIAGNOSTICS v_deleted_count = ROW_COUNT;
    RETURN v_deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Cleanup expired cache entries
CREATE OR REPLACE FUNCTION tool_catalog.cleanup_expired_cache()
RETURNS INTEGER AS $$
DECLARE
    v_deleted_count INTEGER;
BEGIN
    DELETE FROM tool_catalog.tool_cache
    WHERE expires_at < CURRENT_TIMESTAMP;
    
    GET DIAGNOSTICS v_deleted_count = ROW_COUNT;
    RETURN v_deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- COMPLETE
-- ============================================================================

-- Verify schema creation
DO $$
BEGIN
    RAISE NOTICE 'Tool Catalog Schema created successfully!';
    RAISE NOTICE 'Tables: tools, tool_capabilities, tool_patterns, tool_telemetry, tool_ab_tests, tool_audit_log, tool_cache';
    RAISE NOTICE 'Views: v_latest_tools, v_tool_performance, v_catalog_summary';
    RAISE NOTICE 'Functions: get_tool_by_name, search_by_capability, record_telemetry';
    RAISE NOTICE 'Ready to import tools from YAML files using: python scripts/migrate_tools_to_db.py';
END $$;