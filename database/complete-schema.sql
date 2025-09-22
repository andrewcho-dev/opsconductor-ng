-- OpsConductor - Complete Database Schema
-- This file contains ALL tables, indexes, functions, and initial data
-- Required for a fresh installation to work completely

-- Create schemas for each service
CREATE SCHEMA IF NOT EXISTS identity;
CREATE SCHEMA IF NOT EXISTS assets;
CREATE SCHEMA IF NOT EXISTS automation;
CREATE SCHEMA IF NOT EXISTS communication;
CREATE SCHEMA IF NOT EXISTS network_analysis;

-- ============================================================================
-- IDENTITY SERVICE SCHEMA
-- ============================================================================

-- Users table
CREATE TABLE IF NOT EXISTS identity.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    telephone VARCHAR(20),
    title VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    is_admin BOOLEAN DEFAULT false,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Roles table
CREATE TABLE IF NOT EXISTS identity.roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    permissions JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User roles mapping
CREATE TABLE IF NOT EXISTS identity.user_roles (
    user_id INTEGER REFERENCES identity.users(id) ON DELETE CASCADE,
    role_id INTEGER REFERENCES identity.roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    assigned_by INTEGER REFERENCES identity.users(id),
    PRIMARY KEY (user_id, role_id)
);

-- User sessions
CREATE TABLE IF NOT EXISTS identity.user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER REFERENCES identity.users(id) ON DELETE CASCADE,
    refresh_token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_agent TEXT,
    ip_address INET
);

-- User preferences
CREATE TABLE IF NOT EXISTS identity.user_preferences (
    user_id INTEGER PRIMARY KEY REFERENCES identity.users(id) ON DELETE CASCADE,
    preferences JSONB DEFAULT '{}',
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

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
    password_encrypted TEXT,
    private_key_encrypted TEXT,
    public_key TEXT,
    api_key_encrypted TEXT,
    bearer_token_encrypted TEXT,
    certificate_encrypted TEXT,
    passphrase_encrypted TEXT,
    domain VARCHAR(255), -- For Windows domain authentication
    
    -- Additional Services (each with their own single credential)
    additional_services JSONB DEFAULT '[]', -- Array of service objects, each with ONE credential
    
    -- Status and Metadata
    is_active BOOLEAN DEFAULT true,
    connection_status VARCHAR(50), -- 'unknown', 'connected', 'failed', 'timeout'
    last_tested_at TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    
    -- Audit Fields
    created_by INTEGER, -- Reference to identity.users(id)
    updated_by INTEGER, -- Reference to identity.users(id)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- AUTOMATION SERVICE SCHEMA
-- ============================================================================

-- Jobs/Workflows
CREATE TABLE IF NOT EXISTS automation.jobs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    job_type VARCHAR(50) NOT NULL DEFAULT 'general',
    workflow_definition JSONB NOT NULL,
    schedule_expression VARCHAR(255), -- Cron expression
    is_enabled BOOLEAN DEFAULT true,
    tags JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    created_by INTEGER NOT NULL,
    updated_by INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Job executions
CREATE TABLE IF NOT EXISTS automation.job_executions (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES automation.jobs(id) ON DELETE CASCADE,
    execution_id UUID UNIQUE DEFAULT gen_random_uuid(),
    status VARCHAR(50) DEFAULT 'queued', -- 'queued', 'running', 'completed', 'failed', 'cancelled'
    trigger_type VARCHAR(50) NOT NULL, -- 'manual', 'scheduled', 'webhook', 'api'
    input_data JSONB DEFAULT '{}',
    output_data JSONB DEFAULT '{}',
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    started_by INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Step executions (for detailed tracking)
CREATE TABLE IF NOT EXISTS automation.step_executions (
    id SERIAL PRIMARY KEY,
    job_execution_id INTEGER REFERENCES automation.job_executions(id) ON DELETE CASCADE,
    step_id VARCHAR(255) NOT NULL,
    step_name VARCHAR(255) NOT NULL,
    step_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    input_data JSONB DEFAULT '{}',
    output_data JSONB DEFAULT '{}',
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    execution_order INTEGER NOT NULL
);

-- Job schedules
CREATE TABLE IF NOT EXISTS automation.job_schedules (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES automation.jobs(id) ON DELETE CASCADE,
    schedule_expression VARCHAR(255) NOT NULL,
    timezone VARCHAR(100) DEFAULT 'UTC',
    is_active BOOLEAN DEFAULT true,
    next_run_at TIMESTAMP WITH TIME ZONE,
    last_run_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- COMMUNICATION SERVICE SCHEMA
-- ============================================================================

-- Notification templates
CREATE TABLE IF NOT EXISTS communication.notification_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    template_type VARCHAR(50) NOT NULL, -- 'email', 'webhook', 'slack'
    subject_template TEXT,
    body_template TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Notification channels
CREATE TABLE IF NOT EXISTS communication.notification_channels (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    channel_type VARCHAR(50) NOT NULL, -- 'email', 'webhook', 'slack'
    configuration JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Notifications
CREATE TABLE IF NOT EXISTS communication.notifications (
    id SERIAL PRIMARY KEY,
    notification_id UUID UNIQUE DEFAULT gen_random_uuid(),
    template_id INTEGER REFERENCES communication.notification_templates(id),
    channel_id INTEGER REFERENCES communication.notification_channels(id),
    recipient VARCHAR(255) NOT NULL,
    subject VARCHAR(500),
    message TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'sent', 'failed', 'retrying'
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    scheduled_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Audit logs
CREATE TABLE IF NOT EXISTS communication.audit_logs (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    entity_id VARCHAR(255) NOT NULL,
    user_id INTEGER,
    action VARCHAR(100) NOT NULL,
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Identity service indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON identity.users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON identity.users(username);
CREATE INDEX IF NOT EXISTS idx_users_active ON identity.users(is_active);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON identity.user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON identity.user_sessions(expires_at);

-- Assets service indexes (consolidated)
CREATE INDEX IF NOT EXISTS idx_assets_hostname ON assets.assets(hostname);
CREATE INDEX IF NOT EXISTS idx_assets_ip_address ON assets.assets(ip_address);
CREATE INDEX IF NOT EXISTS idx_assets_os_type ON assets.assets(os_type);
CREATE INDEX IF NOT EXISTS idx_assets_service_type ON assets.assets(service_type);
CREATE INDEX IF NOT EXISTS idx_assets_is_active ON assets.assets(is_active);
CREATE INDEX IF NOT EXISTS idx_assets_created_at ON assets.assets(created_at);
CREATE INDEX IF NOT EXISTS idx_assets_tags ON assets.assets USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_assets_additional_services ON assets.assets USING GIN(additional_services);

-- Automation service indexes
CREATE INDEX IF NOT EXISTS idx_jobs_enabled ON automation.jobs(is_enabled);
CREATE INDEX IF NOT EXISTS idx_jobs_created_by ON automation.jobs(created_by);
CREATE INDEX IF NOT EXISTS idx_jobs_job_type ON automation.jobs(job_type);
CREATE INDEX IF NOT EXISTS idx_job_executions_job_id ON automation.job_executions(job_id);
CREATE INDEX IF NOT EXISTS idx_job_executions_status ON automation.job_executions(status);
CREATE INDEX IF NOT EXISTS idx_job_executions_created_at ON automation.job_executions(created_at);
CREATE INDEX IF NOT EXISTS idx_step_executions_job_execution_id ON automation.step_executions(job_execution_id);

-- Communication service indexes
CREATE INDEX IF NOT EXISTS idx_notifications_status ON communication.notifications(status);
CREATE INDEX IF NOT EXISTS idx_notifications_scheduled_at ON communication.notifications(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity ON communication.audit_logs(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON communication.audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON communication.audit_logs(created_at);

-- ============================================================================
-- FUNCTIONS AND TRIGGERS
-- ============================================================================

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update updated_at for assets
DROP TRIGGER IF EXISTS trigger_assets_updated_at ON assets.assets;
CREATE TRIGGER trigger_assets_updated_at
    BEFORE UPDATE ON assets.assets
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- INITIAL DATA
-- ============================================================================

-- Create default admin user (password: admin123)
INSERT INTO identity.users (username, email, password_hash, first_name, last_name, is_admin) 
VALUES ('admin', 'admin@opsconductor.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/SJx/6tZrm', 'System', 'Administrator', true)
ON CONFLICT (username) DO NOTHING;

-- Create default roles
INSERT INTO identity.roles (name, description, permissions, is_active) VALUES 
('admin', 'System Administrator', '["*"]', true),
('manager', 'Team Manager', '[
  "jobs:read", "jobs:create", "jobs:update", "jobs:execute",
  "targets:read", "targets:create", "targets:update",
  "executions:read", "users:read",
  "network:analysis:read", "network:monitoring:read"
]', true),
('operator', 'System Operator', '[
  "jobs:read", "jobs:create", "jobs:update", "jobs:execute", "jobs:delete",
  "targets:read", "targets:create", "targets:update", "targets:delete",
  "executions:read",
  "network:analysis:read", "network:analysis:write",
  "network:monitoring:read", "network:monitoring:write",
  "network:capture:start", "network:capture:stop"
]', true),
('developer', 'Developer', '[
  "jobs:read", "jobs:create", "jobs:update", "jobs:execute",
  "targets:read", "executions:read",
  "network:analysis:read", "network:monitoring:read"
]', true),
('viewer', 'Read-only User', '[
  "jobs:read", "targets:read", "executions:read"
]', true)
ON CONFLICT (name) DO UPDATE SET
    description = EXCLUDED.description,
    permissions = EXCLUDED.permissions,
    is_active = EXCLUDED.is_active;

-- Assign admin role to admin user
INSERT INTO identity.user_roles (user_id, role_id, assigned_by) 
SELECT u.id, r.id, u.id
FROM identity.users u, identity.roles r
WHERE u.username = 'admin' AND r.name = 'admin'
ON CONFLICT (user_id, role_id) DO NOTHING;

-- Create default notification templates
INSERT INTO communication.notification_templates (name, template_type, subject_template, body_template, created_by) 
SELECT 'job_success', 'email', 'Job Completed Successfully: {{job_name}}', 'Job "{{job_name}}" completed successfully at {{completed_at}}.', u.id
FROM identity.users u WHERE u.username = 'admin'
ON CONFLICT (name) DO NOTHING;

INSERT INTO communication.notification_templates (name, template_type, subject_template, body_template, created_by) 
SELECT 'job_failure', 'email', 'Job Failed: {{job_name}}', 'Job "{{job_name}}" failed with error: {{error_message}}', u.id
FROM identity.users u WHERE u.username = 'admin'
ON CONFLICT (name) DO NOTHING;

INSERT INTO communication.notification_templates (name, template_type, subject_template, body_template, created_by) 
SELECT 'system_alert', 'email', 'System Alert: {{alert_type}}', 'System alert: {{message}}', u.id
FROM identity.users u WHERE u.username = 'admin'
ON CONFLICT (name) DO NOTHING;

-- No additional initial data needed for consolidated assets table

-- ============================================================================
-- NETWORK ANALYSIS SERVICE SCHEMA
-- ============================================================================

-- Remote Probes Table
CREATE TABLE IF NOT EXISTS network_analysis.remote_probes (
    id SERIAL PRIMARY KEY,
    probe_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    ip_address VARCHAR(45),
    hostname VARCHAR(255),
    os_type VARCHAR(50),
    version VARCHAR(100),
    capabilities JSONB DEFAULT '[]',
    interfaces JSONB DEFAULT '[]',
    status VARCHAR(50) DEFAULT 'active',
    registered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_heartbeat TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Capture Sessions Table
CREATE TABLE IF NOT EXISTS network_analysis.capture_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    probe_id VARCHAR(255) REFERENCES network_analysis.remote_probes(probe_id),
    user_id INTEGER,
    interface_name VARCHAR(100),
    filter_expression TEXT,
    duration INTEGER,
    packet_count INTEGER,
    status VARCHAR(50) DEFAULT 'starting',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    configuration JSONB DEFAULT '{}',
    results_summary JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Capture Results Table
CREATE TABLE IF NOT EXISTS network_analysis.capture_results (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) REFERENCES network_analysis.capture_sessions(session_id),
    probe_id VARCHAR(255) REFERENCES network_analysis.remote_probes(probe_id),
    packet_data JSONB,
    statistics JSONB DEFAULT '{}',
    ai_analysis JSONB DEFAULT '{}',
    file_path TEXT,
    file_size BIGINT,
    packet_count INTEGER DEFAULT 0,
    bytes_captured BIGINT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Network Monitoring Data Table
CREATE TABLE IF NOT EXISTS network_analysis.monitoring_data (
    id SERIAL PRIMARY KEY,
    probe_id VARCHAR(255) REFERENCES network_analysis.remote_probes(probe_id),
    interface_name VARCHAR(100),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    rx_bytes BIGINT DEFAULT 0,
    tx_bytes BIGINT DEFAULT 0,
    rx_packets BIGINT DEFAULT 0,
    tx_packets BIGINT DEFAULT 0,
    rx_errors BIGINT DEFAULT 0,
    tx_errors BIGINT DEFAULT 0,
    bandwidth_utilization FLOAT,
    latency_ms FLOAT,
    packet_loss_rate FLOAT,
    active_connections INTEGER,
    metrics JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Network Alerts Table
CREATE TABLE IF NOT EXISTS network_analysis.network_alerts (
    id SERIAL PRIMARY KEY,
    alert_id VARCHAR(255) UNIQUE NOT NULL,
    probe_id VARCHAR(255) REFERENCES network_analysis.remote_probes(probe_id),
    alert_type VARCHAR(100) NOT NULL,
    severity VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    source VARCHAR(255),
    interface_name VARCHAR(100),
    threshold_value FLOAT,
    current_value FLOAT,
    status VARCHAR(50) DEFAULT 'active',
    resolved BOOLEAN DEFAULT false,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by INTEGER,
    resolution_notes TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Analysis Jobs Table
CREATE TABLE IF NOT EXISTS network_analysis.analysis_jobs (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(255) UNIQUE NOT NULL,
    probe_id VARCHAR(255) REFERENCES network_analysis.remote_probes(probe_id),
    user_id INTEGER,
    job_type VARCHAR(100) NOT NULL,
    parameters JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'pending',
    priority INTEGER DEFAULT 5,
    scheduled_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    results JSONB DEFAULT '{}',
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
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

-- Triggers for updated_at columns
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

COMMIT;