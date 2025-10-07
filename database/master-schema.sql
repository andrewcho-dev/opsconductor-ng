-- OpsConductor - Complete Database Schema (Keycloak Only)
-- This file contains ALL tables, indexes, functions, and initial data
-- Identity management is handled ENTIRELY by Keycloak

-- Create schemas for each service (NO identity schema needed)
CREATE SCHEMA IF NOT EXISTS assets;
CREATE SCHEMA IF NOT EXISTS automation;
CREATE SCHEMA IF NOT EXISTS communication;
CREATE SCHEMA IF NOT EXISTS network_analysis;
CREATE SCHEMA IF NOT EXISTS keycloak;

-- ============================================================================
-- NO IDENTITY SERVICE SCHEMA - USE KEYCLOAK ONLY
-- ============================================================================
-- All user management, roles, permissions handled by Keycloak
-- No local user/role tables needed

-- ============================================================================
-- ASSETS SERVICE SCHEMA - CONSOLIDATED
-- ============================================================================

-- Consolidated assets table containing all target/asset information
CREATE TABLE IF NOT EXISTS assets.assets (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Basic Asset Information
    name VARCHAR(255) NOT NULL,
    hostname VARCHAR(255) NOT NULL,
    ip_address VARCHAR(45), -- IPv4 or IPv6
    description TEXT,
    tags JSONB DEFAULT '[]',
    
    -- Operating System Information
    os_type VARCHAR(50) DEFAULT 'other', -- 'windows', 'linux', 'unix', 'macos', 'other'
    os_version VARCHAR(100),
    
    -- Primary Connection Service
    service_type VARCHAR(100) NOT NULL, -- 'ssh', 'rdp', 'winrm', 'http', 'https', etc.
    port INTEGER NOT NULL,
    is_secure BOOLEAN DEFAULT false,
    
    -- Primary Service Credentials (ONE credential type per service)
    credential_type VARCHAR(50), -- 'username_password', 'ssh_key', 'api_key', 'bearer_token', 'certificate'
    username VARCHAR(255),
    password_encrypted TEXT, -- Encrypted password
    ssh_private_key_encrypted TEXT, -- Encrypted SSH private key
    ssh_passphrase_encrypted TEXT, -- Encrypted SSH key passphrase
    api_key_encrypted TEXT, -- Encrypted API key
    bearer_token_encrypted TEXT, -- Encrypted bearer token
    certificate_encrypted TEXT, -- Encrypted certificate
    certificate_key_encrypted TEXT, -- Encrypted certificate private key
    
    -- Additional Metadata
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'inactive', 'maintenance'
    last_tested TIMESTAMP WITH TIME ZONE,
    test_result VARCHAR(20), -- 'success', 'failed', 'timeout', null
    test_message TEXT,
    notes TEXT,
    
    -- Discovery Information
    discovered_by VARCHAR(100), -- 'manual', 'network_scan', 'import'
    discovery_source VARCHAR(255), -- source system/scan that discovered this asset
    
    -- Asset Grouping and Environment
    environment VARCHAR(50) DEFAULT 'production', -- 'production', 'staging', 'development', 'test'
    criticality VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high', 'critical'
    asset_group VARCHAR(100), -- Logical grouping (e.g., 'web_servers', 'databases')
    location VARCHAR(100), -- Physical/logical location
    
    -- Automation Integration
    automation_enabled BOOLEAN DEFAULT true,
    automation_tags JSONB DEFAULT '[]', -- Tags specifically for automation targeting
    
    -- Tracking
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100), -- User who created this asset
    updated_by VARCHAR(100)  -- User who last updated this asset
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_assets_hostname ON assets.assets(hostname);
CREATE INDEX IF NOT EXISTS idx_assets_ip_address ON assets.assets(ip_address);
CREATE INDEX IF NOT EXISTS idx_assets_service_type ON assets.assets(service_type);
CREATE INDEX IF NOT EXISTS idx_assets_status ON assets.assets(status);
CREATE INDEX IF NOT EXISTS idx_assets_environment ON assets.assets(environment);
CREATE INDEX IF NOT EXISTS idx_assets_asset_group ON assets.assets(asset_group);
CREATE INDEX IF NOT EXISTS idx_assets_tags ON assets.assets USING GIN (tags);
CREATE INDEX IF NOT EXISTS idx_assets_automation_tags ON assets.assets USING GIN (automation_tags);
CREATE INDEX IF NOT EXISTS idx_assets_created_at ON assets.assets(created_at);
CREATE INDEX IF NOT EXISTS idx_assets_last_tested ON assets.assets(last_tested);

-- ============================================================================
-- AUTOMATION SERVICE SCHEMA
-- ============================================================================

-- Jobs table
CREATE TABLE IF NOT EXISTS automation.jobs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    steps JSONB NOT NULL DEFAULT '[]',
    parameters JSONB DEFAULT '{}',
    tags JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_by VARCHAR(100)
);

-- Job runs table
CREATE TABLE IF NOT EXISTS automation.job_runs (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES automation.jobs(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed', 'cancelled'
    parameters JSONB DEFAULT '{}',
    output JSONB DEFAULT '{}',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_by VARCHAR(100),
    execution_context JSONB DEFAULT '{}'
);

-- Job run steps
CREATE TABLE IF NOT EXISTS automation.job_run_steps (
    id SERIAL PRIMARY KEY,
    job_run_id INTEGER REFERENCES automation.job_runs(id) ON DELETE CASCADE,
    step_name VARCHAR(255) NOT NULL,
    step_type VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    input_data JSONB DEFAULT '{}',
    output_data JSONB DEFAULT '{}',
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_jobs_name ON automation.jobs(name);
CREATE INDEX IF NOT EXISTS idx_jobs_is_active ON automation.jobs(is_active);
CREATE INDEX IF NOT EXISTS idx_jobs_tags ON automation.jobs USING GIN (tags);
CREATE INDEX IF NOT EXISTS idx_job_runs_job_id ON automation.job_runs(job_id);
CREATE INDEX IF NOT EXISTS idx_job_runs_status ON automation.job_runs(status);
CREATE INDEX IF NOT EXISTS idx_job_runs_started_at ON automation.job_runs(started_at);
CREATE INDEX IF NOT EXISTS idx_job_run_steps_job_run_id ON automation.job_run_steps(job_run_id);
CREATE INDEX IF NOT EXISTS idx_job_run_steps_status ON automation.job_run_steps(status);

-- ============================================================================
-- COMMUNICATION SERVICE SCHEMA
-- ============================================================================

-- Communication channels
CREATE TABLE IF NOT EXISTS communication.channels (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    type VARCHAR(50) NOT NULL, -- 'email', 'slack', 'teams', 'discord', 'webhook'
    configuration JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Message templates
CREATE TABLE IF NOT EXISTS communication.templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    subject VARCHAR(255),
    body TEXT NOT NULL,
    template_type VARCHAR(50) NOT NULL, -- 'job_success', 'job_failure', 'system_alert', etc.
    variables JSONB DEFAULT '[]', -- Array of variable names used in template
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Notifications/messages sent
CREATE TABLE IF NOT EXISTS communication.notifications (
    id SERIAL PRIMARY KEY,
    channel_id INTEGER REFERENCES communication.channels(id),
    template_id INTEGER REFERENCES communication.templates(id),
    recipient VARCHAR(255) NOT NULL,
    subject VARCHAR(255),
    message TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'sent', 'failed', 'retrying'
    sent_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- Audit logs
CREATE TABLE IF NOT EXISTS communication.audit_logs (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL, -- From Keycloak
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_channels_name ON communication.channels(name);
CREATE INDEX IF NOT EXISTS idx_channels_type ON communication.channels(type);
CREATE INDEX IF NOT EXISTS idx_templates_name ON communication.templates(name);
CREATE INDEX IF NOT EXISTS idx_templates_type ON communication.templates(template_type);
CREATE INDEX IF NOT EXISTS idx_notifications_channel_id ON communication.notifications(channel_id);
CREATE INDEX IF NOT EXISTS idx_notifications_status ON communication.notifications(status);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON communication.notifications(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON communication.audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON communication.audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON communication.audit_logs(created_at);

-- ============================================================================
-- NETWORK ANALYSIS SERVICE SCHEMA
-- ============================================================================

-- Remote network analysis probes
CREATE TABLE IF NOT EXISTS network_analysis.remote_probes (
    id SERIAL PRIMARY KEY,
    probe_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    status VARCHAR(20) DEFAULT 'inactive', -- 'active', 'inactive', 'error'
    last_heartbeat TIMESTAMP WITH TIME ZONE,
    configuration JSONB DEFAULT '{}',
    capabilities JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Network capture sessions
CREATE TABLE IF NOT EXISTS network_analysis.capture_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    probe_id VARCHAR(100) REFERENCES network_analysis.remote_probes(probe_id),
    target_network VARCHAR(100),
    capture_filter VARCHAR(500),
    status VARCHAR(20) DEFAULT 'scheduled', -- 'scheduled', 'active', 'completed', 'failed'
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    packets_captured INTEGER DEFAULT 0,
    data_size_bytes BIGINT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- Network monitoring data
CREATE TABLE IF NOT EXISTS network_analysis.monitoring_data (
    id SERIAL PRIMARY KEY,
    probe_id VARCHAR(100) REFERENCES network_analysis.remote_probes(probe_id),
    metric_name VARCHAR(100) NOT NULL,
    metric_value JSONB NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    tags JSONB DEFAULT '{}'
);

-- Network alerts and anomalies
CREATE TABLE IF NOT EXISTS network_analysis.network_alerts (
    id SERIAL PRIMARY KEY,
    probe_id VARCHAR(100) REFERENCES network_analysis.remote_probes(probe_id),
    alert_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL, -- 'low', 'medium', 'high', 'critical'
    message TEXT NOT NULL,
    details JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'open', -- 'open', 'acknowledged', 'resolved', 'false_positive'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    resolved_at TIMESTAMP WITH TIME ZONE
);

-- Network analysis jobs
CREATE TABLE IF NOT EXISTS network_analysis.analysis_jobs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    job_type VARCHAR(100) NOT NULL, -- 'port_scan', 'vulnerability_scan', 'traffic_analysis'
    target VARCHAR(255) NOT NULL,
    parameters JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'scheduled',
    results JSONB DEFAULT '{}',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_remote_probes_probe_id ON network_analysis.remote_probes(probe_id);
CREATE INDEX IF NOT EXISTS idx_remote_probes_status ON network_analysis.remote_probes(status);
CREATE INDEX IF NOT EXISTS idx_remote_probes_last_heartbeat ON network_analysis.remote_probes(last_heartbeat);

CREATE INDEX IF NOT EXISTS idx_capture_sessions_session_id ON network_analysis.capture_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_capture_sessions_probe_id ON network_analysis.capture_sessions(probe_id);
CREATE INDEX IF NOT EXISTS idx_capture_sessions_status ON network_analysis.capture_sessions(status);

CREATE INDEX IF NOT EXISTS idx_monitoring_data_probe_id ON network_analysis.monitoring_data(probe_id);
CREATE INDEX IF NOT EXISTS idx_monitoring_data_timestamp ON network_analysis.monitoring_data(timestamp);

CREATE INDEX IF NOT EXISTS idx_network_alerts_probe_id ON network_analysis.network_alerts(probe_id);
CREATE INDEX IF NOT EXISTS idx_network_alerts_status ON network_analysis.network_alerts(status);

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to update updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at columns
CREATE TRIGGER trigger_assets_updated_at
    BEFORE UPDATE ON assets.assets
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_jobs_updated_at
    BEFORE UPDATE ON automation.jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_channels_updated_at
    BEFORE UPDATE ON communication.channels
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_templates_updated_at
    BEFORE UPDATE ON communication.templates
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_remote_probes_updated_at
    BEFORE UPDATE ON network_analysis.remote_probes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_capture_sessions_updated_at
    BEFORE UPDATE ON network_analysis.capture_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_network_alerts_updated_at
    BEFORE UPDATE ON network_analysis.network_alerts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_analysis_jobs_updated_at
    BEFORE UPDATE ON network_analysis.analysis_jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- INITIAL DATA (Minimal - No Users/Roles)
-- ============================================================================

-- Insert default communication channels
INSERT INTO communication.channels (name, type, configuration, is_active) VALUES 
('default-email', 'email', '{"smtp_server": "localhost", "smtp_port": 587, "use_tls": true}', true),
('system-webhook', 'webhook', '{"url": "http://localhost:8080/api/webhooks/system", "headers": {}}', false)
ON CONFLICT (name) DO NOTHING;

-- Insert default templates
INSERT INTO communication.templates (name, subject, body, template_type, variables, is_active) VALUES 
('job_success', 'Job Completed Successfully', 'Job {{job_name}} completed successfully at {{completion_time}}.', 'job_success', '["job_name", "completion_time"]', true),
('job_failure', 'Job Failed', 'Job {{job_name}} failed with error: {{error_message}}', 'job_failure', '["job_name", "error_message"]', true),
('system_alert', 'System Alert', 'System alert: {{alert_message}}', 'system_alert', '["alert_message"]', true)
ON CONFLICT (name) DO NOTHING;

COMMIT;-- ============================================================================
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
    expected_outputs JSONB DEFAULT '[]',
    
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
END $$;-- ============================================================================
-- PHASE 7: STAGE E EXECUTION SCHEMA
-- Production-hardened execution architecture with 7 critical safety features
-- ============================================================================

-- Create execution schema
CREATE SCHEMA IF NOT EXISTS execution;

-- ============================================================================
-- ENUMS (Create first, referenced by tables)
-- ============================================================================

-- Execution status with FSM legal transitions
CREATE TYPE execution.execution_status AS ENUM (
    'pending_approval',  -- Initial state for Level 1-3
    'approved',          -- Approved, ready to execute
    'rejected',          -- Rejected by approver
    'queued',            -- In background queue
    'running',           -- Currently executing
    'completed',         -- Successfully completed
    'failed',            -- Failed with error
    'cancelled',         -- Cancelled by user
    'timeout',           -- Exceeded timeout policy
    'partial'            -- Some steps succeeded, some failed
);

-- Execution mode (immediate vs background)
CREATE TYPE execution.execution_mode AS ENUM (
    'immediate',   -- Synchronous execution (<10s)
    'background'   -- Asynchronous execution (>30s, via queue)
);

-- SLA class for timeout policies
CREATE TYPE execution.sla_class AS ENUM (
    'fast',    -- <10s operations
    'medium',  -- 10-30s operations
    'long'     -- >30s operations
);

-- Approval state
CREATE TYPE execution.approval_state AS ENUM (
    'pending',   -- Awaiting approval
    'approved',  -- Approved
    'rejected',  -- Rejected
    'expired'    -- Approval window expired
);

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- Executions table (main execution records)
CREATE TABLE execution.executions (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    execution_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    
    -- Tenant & Actor (for multi-tenancy)
    tenant_id VARCHAR(255) NOT NULL,
    actor_id INTEGER NOT NULL, -- Reference to identity.users(id)
    
    -- Idempotency
    idempotency_key VARCHAR(64) NOT NULL, -- sha256(canonical_json(plan) + tenant_id + actor_id)
    plan_snapshot JSONB NOT NULL, -- Immutable snapshot of the plan
    
    -- Execution Metadata
    execution_mode execution.execution_mode NOT NULL,
    sla_class execution.sla_class NOT NULL,
    approval_level INTEGER NOT NULL CHECK (approval_level BETWEEN 0 AND 3),
    
    -- Status & FSM
    status execution.execution_status NOT NULL DEFAULT 'pending_approval',
    previous_status execution.execution_status, -- For audit trail
    status_changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Timing
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    timeout_at TIMESTAMP WITH TIME ZONE, -- Calculated from timeout_policies
    
    -- Results
    result JSONB, -- Final execution result
    error_message TEXT,
    error_details JSONB,
    
    -- Observability
    trace_id UUID, -- For distributed tracing
    parent_execution_id UUID, -- For nested executions
    tags JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    
    -- Audit
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT unique_idempotency_per_tenant UNIQUE (tenant_id, idempotency_key),
    CONSTRAINT valid_approval_level CHECK (approval_level IN (0, 1, 2, 3))
);

-- Execution steps table (step-level tracking)
CREATE TABLE execution.execution_steps (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    step_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    
    -- Foreign Key
    execution_id UUID NOT NULL REFERENCES execution.executions(execution_id) ON DELETE CASCADE,
    
    -- Step Metadata
    step_index INTEGER NOT NULL, -- Order in the plan
    step_name VARCHAR(255) NOT NULL,
    step_type VARCHAR(100) NOT NULL, -- 'ssh_command', 'api_call', 'file_transfer', etc.
    target_asset_id INTEGER, -- Reference to assets.assets(id)
    target_hostname VARCHAR(255),
    
    -- Status
    status execution.execution_status NOT NULL DEFAULT 'queued',
    
    -- Timing
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,
    
    -- Input/Output
    input_data JSONB,
    output_data JSONB,
    artifacts JSONB, -- Limited to 10KB per step
    
    -- Error Handling
    error_message TEXT,
    error_details JSONB,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    
    -- Observability
    trace_id UUID,
    logs TEXT, -- Masked logs
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT unique_step_per_execution UNIQUE (execution_id, step_index)
);

-- Approvals table (approval workflow)
CREATE TABLE execution.approvals (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    approval_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    
    -- Foreign Key
    execution_id UUID NOT NULL REFERENCES execution.executions(execution_id) ON DELETE CASCADE,
    
    -- Approval Metadata
    approval_level INTEGER NOT NULL CHECK (approval_level BETWEEN 1 AND 3),
    plan_hash VARCHAR(64) NOT NULL, -- Bound to plan snapshot
    
    -- Approver
    approver_id INTEGER, -- Reference to identity.users(id), NULL if pending
    approver_comment TEXT,
    
    -- State
    state execution.approval_state NOT NULL DEFAULT 'pending',
    
    -- Timing
    requested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE, -- Approval window
    responded_at TIMESTAMP WITH TIME ZONE,
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT one_approval_per_execution UNIQUE (execution_id)
);

-- Execution events table (audit trail for FSM transitions)
CREATE TABLE execution.execution_events (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    event_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    
    -- Foreign Key
    execution_id UUID NOT NULL REFERENCES execution.executions(execution_id) ON DELETE CASCADE,
    
    -- Event Metadata
    event_type VARCHAR(100) NOT NULL, -- 'status_change', 'approval', 'cancellation', 'timeout', etc.
    from_status execution.execution_status,
    to_status execution.execution_status,
    
    -- Actor
    actor_id INTEGER, -- Reference to identity.users(id)
    actor_type VARCHAR(50), -- 'user', 'system', 'worker'
    
    -- Details
    details JSONB,
    error_message TEXT,
    
    -- Timing
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Observability
    trace_id UUID
);

-- ============================================================================
-- BACKGROUND QUEUE TABLES
-- ============================================================================

-- Execution queue (Redis-backed, PostgreSQL for persistence)
CREATE TABLE execution.execution_queue (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    queue_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    
    -- Foreign Key
    execution_id UUID NOT NULL REFERENCES execution.executions(execution_id) ON DELETE CASCADE,
    
    -- Queue Metadata
    priority INTEGER DEFAULT 5, -- 1 (highest) to 10 (lowest)
    sla_class execution.sla_class NOT NULL,
    
    -- Lease Management
    lease_token UUID, -- Worker lease token
    lease_expires_at TIMESTAMP WITH TIME ZONE, -- Lease timeout
    visibility_timeout_seconds INTEGER, -- Calculated from timeout_policies
    
    -- Retry Logic
    attempt_count INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3, -- Based on SLA class
    last_error TEXT,
    
    -- Timing
    enqueued_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    dequeued_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Status
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT unique_execution_in_queue UNIQUE (execution_id)
);

-- Dead letter queue (DLQ for failed executions)
CREATE TABLE execution.execution_dlq (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    dlq_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    
    -- Foreign Key
    execution_id UUID NOT NULL REFERENCES execution.executions(execution_id) ON DELETE CASCADE,
    
    -- Failure Metadata
    failure_reason TEXT NOT NULL,
    failure_details JSONB,
    attempt_count INTEGER NOT NULL,
    last_error TEXT,
    
    -- Original Queue Entry
    original_queue_id UUID,
    sla_class execution.sla_class NOT NULL,
    
    -- Timing
    failed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Retry/Requeue
    requeued BOOLEAN DEFAULT false,
    requeued_at TIMESTAMP WITH TIME ZONE,
    requeued_by INTEGER, -- Reference to identity.users(id)
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT unique_execution_in_dlq UNIQUE (execution_id)
);

-- ============================================================================
-- SAFETY TABLES
-- ============================================================================

-- Execution locks (per-asset mutex)
CREATE TABLE execution.execution_locks (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    lock_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    
    -- Lock Target
    asset_id INTEGER NOT NULL, -- Reference to assets.assets(id)
    tenant_id VARCHAR(255) NOT NULL,
    
    -- Lock Owner
    execution_id UUID NOT NULL REFERENCES execution.executions(execution_id) ON DELETE CASCADE,
    owner_tag VARCHAR(255) NOT NULL, -- Format: "execution:{execution_id}:worker:{worker_id}"
    
    -- Lock Metadata
    acquired_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL, -- TTL for stale lock reaper
    last_heartbeat_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT unique_lock_per_asset_tenant UNIQUE (asset_id, tenant_id)
);

-- Timeout policies (SLA class × action class matrix)
CREATE TABLE execution.timeout_policies (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Policy Key
    sla_class execution.sla_class NOT NULL,
    action_class VARCHAR(50) NOT NULL, -- 'read', 'modify', 'deploy'
    
    -- Timeout Values (in seconds)
    step_timeout_seconds INTEGER NOT NULL,
    execution_timeout_seconds INTEGER NOT NULL,
    lease_timeout_seconds INTEGER NOT NULL, -- For queue workers
    approval_timeout_seconds INTEGER, -- For approval workflows
    
    -- DLQ Thresholds
    max_attempts INTEGER NOT NULL,
    
    -- Metadata
    description TEXT,
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT unique_timeout_policy UNIQUE (sla_class, action_class)
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Executions indexes
CREATE INDEX idx_executions_tenant_id ON execution.executions(tenant_id);
CREATE INDEX idx_executions_actor_id ON execution.executions(actor_id);
CREATE INDEX idx_executions_status ON execution.executions(status);
CREATE INDEX idx_executions_execution_mode ON execution.executions(execution_mode);
CREATE INDEX idx_executions_sla_class ON execution.executions(sla_class);
CREATE INDEX idx_executions_created_at ON execution.executions(created_at);
CREATE INDEX idx_executions_idempotency_key ON execution.executions(tenant_id, idempotency_key);
CREATE INDEX idx_executions_trace_id ON execution.executions(trace_id);

-- Execution steps indexes
CREATE INDEX idx_execution_steps_execution_id ON execution.execution_steps(execution_id);
CREATE INDEX idx_execution_steps_status ON execution.execution_steps(status);
CREATE INDEX idx_execution_steps_target_asset_id ON execution.execution_steps(target_asset_id);
CREATE INDEX idx_execution_steps_step_index ON execution.execution_steps(execution_id, step_index);

-- Approvals indexes
CREATE INDEX idx_approvals_execution_id ON execution.approvals(execution_id);
CREATE INDEX idx_approvals_state ON execution.approvals(state);
CREATE INDEX idx_approvals_approver_id ON execution.approvals(approver_id);
CREATE INDEX idx_approvals_expires_at ON execution.approvals(expires_at);

-- Execution events indexes
CREATE INDEX idx_execution_events_execution_id ON execution.execution_events(execution_id);
CREATE INDEX idx_execution_events_event_type ON execution.execution_events(event_type);
CREATE INDEX idx_execution_events_created_at ON execution.execution_events(created_at);
CREATE INDEX idx_execution_events_trace_id ON execution.execution_events(trace_id);

-- Execution queue indexes
CREATE INDEX idx_execution_queue_execution_id ON execution.execution_queue(execution_id);
CREATE INDEX idx_execution_queue_status ON execution.execution_queue(status);
CREATE INDEX idx_execution_queue_priority ON execution.execution_queue(priority, enqueued_at);
CREATE INDEX idx_execution_queue_lease_expires_at ON execution.execution_queue(lease_expires_at);
CREATE INDEX idx_execution_queue_sla_class ON execution.execution_queue(sla_class);

-- Execution DLQ indexes
CREATE INDEX idx_execution_dlq_execution_id ON execution.execution_dlq(execution_id);
CREATE INDEX idx_execution_dlq_failed_at ON execution.execution_dlq(failed_at);
CREATE INDEX idx_execution_dlq_requeued ON execution.execution_dlq(requeued);

-- Execution locks indexes
CREATE INDEX idx_execution_locks_asset_id ON execution.execution_locks(asset_id);
CREATE INDEX idx_execution_locks_tenant_id ON execution.execution_locks(tenant_id);
CREATE INDEX idx_execution_locks_execution_id ON execution.execution_locks(execution_id);
CREATE INDEX idx_execution_locks_expires_at ON execution.execution_locks(expires_at);
CREATE INDEX idx_execution_locks_is_active ON execution.execution_locks(is_active);

-- Timeout policies indexes
CREATE INDEX idx_timeout_policies_sla_class ON execution.timeout_policies(sla_class);
CREATE INDEX idx_timeout_policies_action_class ON execution.timeout_policies(action_class);

-- ============================================================================
-- INITIAL DATA: TIMEOUT POLICIES
-- ============================================================================

-- Insert default timeout policies (SLA class × action class matrix)
INSERT INTO execution.timeout_policies (sla_class, action_class, step_timeout_seconds, execution_timeout_seconds, lease_timeout_seconds, approval_timeout_seconds, max_attempts, description) VALUES
    -- Fast SLA (read operations)
    ('fast', 'read', 5, 10, 15, 300, 3, 'Fast read operations: <5s per step, <10s total'),
    -- Fast SLA (modify operations)
    ('fast', 'modify', 8, 15, 20, 600, 3, 'Fast modify operations: <8s per step, <15s total'),
    -- Fast SLA (deploy operations)
    ('fast', 'deploy', 10, 20, 30, 900, 3, 'Fast deploy operations: <10s per step, <20s total'),
    
    -- Medium SLA (read operations)
    ('medium', 'read', 15, 30, 45, 600, 5, 'Medium read operations: <15s per step, <30s total'),
    -- Medium SLA (modify operations)
    ('medium', 'modify', 20, 45, 60, 900, 5, 'Medium modify operations: <20s per step, <45s total'),
    -- Medium SLA (deploy operations)
    ('medium', 'deploy', 30, 60, 90, 1800, 5, 'Medium deploy operations: <30s per step, <60s total'),
    
    -- Long SLA (read operations)
    ('long', 'read', 60, 300, 360, 1800, 3, 'Long read operations: <60s per step, <5min total'),
    -- Long SLA (modify operations)
    ('long', 'modify', 120, 600, 720, 3600, 3, 'Long modify operations: <120s per step, <10min total'),
    -- Long SLA (deploy operations)
    ('long', 'deploy', 300, 1800, 2160, 7200, 3, 'Long deploy operations: <5min per step, <30min total');

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON SCHEMA execution IS 'Phase 7: Stage E Execution schema with production-hardened safety features';

COMMENT ON TABLE execution.executions IS 'Main execution records with tenant-scoped idempotency and FSM state machine';
COMMENT ON TABLE execution.execution_steps IS 'Step-level tracking with retry logic and artifact storage (10KB cap)';
COMMENT ON TABLE execution.approvals IS 'Approval workflow with plan hash binding and expiration';
COMMENT ON TABLE execution.execution_events IS 'Audit trail for FSM transitions and execution events';
COMMENT ON TABLE execution.execution_queue IS 'Background execution queue with lease management and retry logic';
COMMENT ON TABLE execution.execution_dlq IS 'Dead letter queue for failed executions requiring manual intervention';
COMMENT ON TABLE execution.execution_locks IS 'Per-asset mutex locks with TTL and stale lock reaper support';
COMMENT ON TABLE execution.timeout_policies IS 'SLA class × action class timeout matrix with DLQ thresholds';

COMMENT ON COLUMN execution.executions.idempotency_key IS 'sha256(canonical_json(plan) + tenant_id + actor_id) for duplicate prevention';
COMMENT ON COLUMN execution.executions.plan_snapshot IS 'Immutable snapshot of the execution plan with deterministic target ordering';
COMMENT ON COLUMN execution.execution_steps.artifacts IS 'Step artifacts limited to 10KB per step';
COMMENT ON COLUMN execution.approvals.plan_hash IS 'Bound to plan snapshot to prevent approval tampering';
COMMENT ON COLUMN execution.execution_locks.owner_tag IS 'Format: execution:{execution_id}:worker:{worker_id}';
COMMENT ON COLUMN execution.timeout_policies.lease_timeout_seconds IS 'Formula: max(step_timeout + buffer, 2× p95_step_duration)';

-- ============================================================================
-- VERIFICATION QUERIES (for GO/NO-GO checklist)
-- ============================================================================

-- Verify ENUMs
DO $$
BEGIN
    RAISE NOTICE 'Verifying ENUMs...';
    ASSERT (SELECT COUNT(*) FROM pg_type WHERE typname = 'execution_status' AND typnamespace = 'execution'::regnamespace) = 1, 'execution_status ENUM not found';
    ASSERT (SELECT COUNT(*) FROM pg_type WHERE typname = 'execution_mode' AND typnamespace = 'execution'::regnamespace) = 1, 'execution_mode ENUM not found';
    ASSERT (SELECT COUNT(*) FROM pg_type WHERE typname = 'sla_class' AND typnamespace = 'execution'::regnamespace) = 1, 'sla_class ENUM not found';
    ASSERT (SELECT COUNT(*) FROM pg_type WHERE typname = 'approval_state' AND typnamespace = 'execution'::regnamespace) = 1, 'approval_state ENUM not found';
    RAISE NOTICE 'ENUMs verified successfully';
END $$;

-- Verify tables
DO $$
BEGIN
    RAISE NOTICE 'Verifying tables...';
    ASSERT (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'execution' AND table_name = 'executions') = 1, 'executions table not found';
    ASSERT (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'execution' AND table_name = 'execution_steps') = 1, 'execution_steps table not found';
    ASSERT (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'execution' AND table_name = 'approvals') = 1, 'approvals table not found';
    ASSERT (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'execution' AND table_name = 'execution_events') = 1, 'execution_events table not found';
    ASSERT (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'execution' AND table_name = 'execution_queue') = 1, 'execution_queue table not found';
    ASSERT (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'execution' AND table_name = 'execution_dlq') = 1, 'execution_dlq table not found';
    ASSERT (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'execution' AND table_name = 'execution_locks') = 1, 'execution_locks table not found';
    ASSERT (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'execution' AND table_name = 'timeout_policies') = 1, 'timeout_policies table not found';
    RAISE NOTICE 'Tables verified successfully';
END $$;

-- Verify indexes
DO $$
BEGIN
    RAISE NOTICE 'Verifying indexes...';
    ASSERT (SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'execution' AND tablename = 'executions') >= 8, 'Missing indexes on executions table';
    ASSERT (SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'execution' AND tablename = 'execution_steps') >= 4, 'Missing indexes on execution_steps table';
    ASSERT (SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'execution' AND tablename = 'approvals') >= 4, 'Missing indexes on approvals table';
    ASSERT (SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'execution' AND tablename = 'execution_events') >= 3, 'Missing indexes on execution_events table';
    ASSERT (SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'execution' AND tablename = 'execution_queue') >= 5, 'Missing indexes on execution_queue table';
    ASSERT (SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'execution' AND tablename = 'execution_dlq') >= 3, 'Missing indexes on execution_dlq table';
    ASSERT (SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'execution' AND tablename = 'execution_locks') >= 5, 'Missing indexes on execution_locks table';
    ASSERT (SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'execution' AND tablename = 'timeout_policies') >= 2, 'Missing indexes on timeout_policies table';
    RAISE NOTICE 'Indexes verified successfully';
END $$;

-- Verify timeout policies data
DO $$
BEGIN
    RAISE NOTICE 'Verifying timeout policies data...';
    ASSERT (SELECT COUNT(*) FROM execution.timeout_policies) = 9, 'Expected 9 timeout policies (3 SLA classes × 3 action classes)';
    RAISE NOTICE 'Timeout policies data verified successfully';
END $$;

RAISE NOTICE '✅ Phase 7 database schema created successfully!';