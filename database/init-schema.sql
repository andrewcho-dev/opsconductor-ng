-- OpsConductor - New Optimized Database Schema
-- Domain-driven design with clear service boundaries

-- Create schemas for each service
CREATE SCHEMA IF NOT EXISTS identity;
CREATE SCHEMA IF NOT EXISTS assets;
CREATE SCHEMA IF NOT EXISTS automation;
CREATE SCHEMA IF NOT EXISTS communication;

-- ============================================================================
-- IDENTITY SERVICE SCHEMA
-- ============================================================================

-- Users table
CREATE TABLE identity.users (
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
CREATE TABLE identity.roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    permissions JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User roles mapping
CREATE TABLE identity.user_roles (
    user_id INTEGER REFERENCES identity.users(id) ON DELETE CASCADE,
    role_id INTEGER REFERENCES identity.roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    assigned_by INTEGER REFERENCES identity.users(id),
    PRIMARY KEY (user_id, role_id)
);

-- User sessions
CREATE TABLE identity.user_sessions (
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
CREATE TABLE identity.user_preferences (
    user_id INTEGER PRIMARY KEY REFERENCES identity.users(id) ON DELETE CASCADE,
    preferences JSONB DEFAULT '{}',
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- ASSETS SERVICE SCHEMA
-- ============================================================================

-- Consolidated Assets Table
-- Replaces: targets, enhanced_targets, target_services
CREATE TABLE assets.assets (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Basic Asset Information
    name VARCHAR(255) NOT NULL,
    hostname VARCHAR(255) NOT NULL,
    ip_address VARCHAR(45), -- IPv4 or IPv6
    description TEXT,
    tags JSONB DEFAULT '[]',
    
    -- Device/Hardware Information
    device_type VARCHAR(50) DEFAULT 'other', -- 'server', 'workstation', 'network_device', 'storage', 'other'
    hardware_make VARCHAR(100),
    hardware_model VARCHAR(100),
    serial_number VARCHAR(100),
    
    -- Operating System Information
    os_type VARCHAR(50) DEFAULT 'other', -- 'windows', 'linux', 'unix', 'macos', 'other'
    os_version VARCHAR(100),
    
    -- Location Information
    physical_address TEXT,
    data_center VARCHAR(100),
    building VARCHAR(100),
    room VARCHAR(100),
    rack_position VARCHAR(50),
    rack_location VARCHAR(100),
    gps_coordinates VARCHAR(100),
    
    -- Status and Management
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'inactive', 'maintenance', 'decommissioned'
    environment VARCHAR(50) DEFAULT 'production', -- 'production', 'staging', 'development', 'test'
    criticality VARCHAR(50) DEFAULT 'medium', -- 'critical', 'high', 'medium', 'low'
    owner VARCHAR(255),
    support_contact VARCHAR(255),
    contract_number VARCHAR(100),
    
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
    
    -- Database-specific fields (for database assets)
    database_type VARCHAR(50), -- 'mysql', 'postgresql', 'sql_server', 'oracle', 'mongodb', etc.
    database_name VARCHAR(255),
    
    -- Secondary Service (legacy support)
    secondary_service_type VARCHAR(100) DEFAULT 'none',
    secondary_port INTEGER,
    ftp_type VARCHAR(50), -- 'ftp', 'ftps', 'sftp'
    secondary_username VARCHAR(255),
    secondary_password_encrypted TEXT,
    
    -- Additional Services (each with their own single credential)
    additional_services JSONB DEFAULT '[]', -- Array of service objects, each with ONE credential
    
    -- Connection Status
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

-- Create indexes for performance
CREATE INDEX idx_assets_hostname ON assets.assets(hostname);
CREATE INDEX idx_assets_ip_address ON assets.assets(ip_address);
CREATE INDEX idx_assets_os_type ON assets.assets(os_type);
CREATE INDEX idx_assets_device_type ON assets.assets(device_type);
CREATE INDEX idx_assets_service_type ON assets.assets(service_type);
CREATE INDEX idx_assets_status ON assets.assets(status);
CREATE INDEX idx_assets_environment ON assets.assets(environment);
CREATE INDEX idx_assets_is_active ON assets.assets(is_active);
CREATE INDEX idx_assets_created_at ON assets.assets(created_at);
CREATE INDEX idx_assets_tags ON assets.assets USING GIN(tags);
CREATE INDEX idx_assets_additional_services ON assets.assets USING GIN(additional_services);

-- Add comments for documentation
COMMENT ON TABLE assets.assets IS 'Consolidated assets table containing all target/asset information including services and credentials';
COMMENT ON COLUMN assets.assets.additional_services IS 'JSON array of additional services, each with their own credentials';
COMMENT ON COLUMN assets.assets.credential_type IS 'Type of credential for primary service: username_password, ssh_key, api_key, bearer_token, certificate';



-- ============================================================================
-- AUTOMATION SERVICE SCHEMA
-- ============================================================================



-- Jobs/Workflows
CREATE TABLE automation.jobs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
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
CREATE TABLE automation.job_executions (
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
CREATE TABLE automation.step_executions (
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
CREATE TABLE automation.job_schedules (
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
CREATE TABLE communication.notification_templates (
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
CREATE TABLE communication.notification_channels (
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
CREATE TABLE communication.notifications (
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
CREATE TABLE communication.audit_logs (
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
CREATE INDEX idx_users_email ON identity.users(email);
CREATE INDEX idx_users_username ON identity.users(username);
CREATE INDEX idx_users_active ON identity.users(is_active);
CREATE INDEX idx_user_sessions_user_id ON identity.user_sessions(user_id);
CREATE INDEX idx_user_sessions_expires_at ON identity.user_sessions(expires_at);

-- Assets service indexes (already created in table definition above)



-- Automation service indexes
CREATE INDEX idx_jobs_enabled ON automation.jobs(is_enabled);
CREATE INDEX idx_jobs_created_by ON automation.jobs(created_by);
CREATE INDEX idx_job_executions_job_id ON automation.job_executions(job_id);
CREATE INDEX idx_job_executions_status ON automation.job_executions(status);
CREATE INDEX idx_job_executions_created_at ON automation.job_executions(created_at);
CREATE INDEX idx_step_executions_job_execution_id ON automation.step_executions(job_execution_id);

-- Communication service indexes
CREATE INDEX idx_notifications_status ON communication.notifications(status);
CREATE INDEX idx_notifications_scheduled_at ON communication.notifications(scheduled_at);
CREATE INDEX idx_audit_logs_entity ON communication.audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_logs_user_id ON communication.audit_logs(user_id);
CREATE INDEX idx_audit_logs_created_at ON communication.audit_logs(created_at);

-- ============================================================================
-- INITIAL DATA
-- ============================================================================

-- Create default admin user (password: admin123)
INSERT INTO identity.users (username, email, password_hash, first_name, last_name, is_admin) 
VALUES ('admin', 'admin@opsconductor.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/SJx/6tZrm', 'System', 'Administrator', true);

-- Create default roles
INSERT INTO identity.roles (name, description, permissions) VALUES 
('admin', 'System Administrator', '["*"]'),
('operator', 'System Operator', '["jobs:read", "jobs:execute", "assets:read"]'),
('viewer', 'Read-only User', '["jobs:read", "assets:read", "executions:read"]');

-- Assign admin role to admin user
INSERT INTO identity.user_roles (user_id, role_id, assigned_by) 
VALUES (1, 1, 1);

-- Create default notification templates
INSERT INTO communication.notification_templates (name, template_type, subject_template, body_template, created_by) VALUES 
('job_success', 'email', 'Job Completed Successfully: {{job_name}}', 'Job "{{job_name}}" completed successfully at {{completed_at}}.', 1),
('job_failure', 'email', 'Job Failed: {{job_name}}', 'Job "{{job_name}}" failed with error: {{error_message}}', 1),
('system_alert', 'email', 'System Alert: {{alert_type}}', 'System alert: {{message}}', 1);

COMMIT;