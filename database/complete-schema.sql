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

COMMIT;