-- OpsConductor - Complete Database Schema
-- This file contains ALL tables, indexes, functions, and initial data
-- Required for a fresh installation to work completely

-- Create schemas for each service
CREATE SCHEMA IF NOT EXISTS identity;
CREATE SCHEMA IF NOT EXISTS assets;
CREATE SCHEMA IF NOT EXISTS automation;
CREATE SCHEMA IF NOT EXISTS communication;

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
-- ASSETS SERVICE SCHEMA
-- ============================================================================

-- Legacy targets table (for backward compatibility)
CREATE TABLE IF NOT EXISTS assets.targets (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    host VARCHAR(255) NOT NULL,
    port INTEGER,
    target_type VARCHAR(50) NOT NULL, -- 'windows', 'linux', 'network', 'cloud'
    connection_type VARCHAR(50) NOT NULL, -- 'ssh', 'winrm', 'http', 'snmp'
    tags JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Enhanced targets (for new UI)
CREATE TABLE IF NOT EXISTS assets.enhanced_targets (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    hostname VARCHAR(255) NOT NULL,
    ip_address VARCHAR(45), -- IPv4 or IPv6
    os_type VARCHAR(50) DEFAULT 'other', -- 'windows', 'linux', 'unix', 'macos', 'other'
    os_version VARCHAR(100),
    description TEXT,
    tags JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Target services (for enhanced targets)
CREATE TABLE IF NOT EXISTS assets.target_services (
    id SERIAL PRIMARY KEY,
    target_id INTEGER REFERENCES assets.enhanced_targets(id) ON DELETE CASCADE,
    service_type VARCHAR(100) NOT NULL, -- 'ssh', 'rdp', 'winrm', 'http', 'https', etc.
    port INTEGER NOT NULL,
    is_default BOOLEAN DEFAULT false,
    is_secure BOOLEAN DEFAULT false,
    is_enabled BOOLEAN DEFAULT true,
    notes TEXT,
    
    -- Embedded credential fields
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
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Constraint: Exactly one default service per target
DROP INDEX IF EXISTS idx_target_services_one_default;
CREATE UNIQUE INDEX idx_target_services_one_default 
ON assets.target_services (target_id) 
WHERE is_default = true;

-- Target credentials table (for legacy compatibility)
CREATE TABLE IF NOT EXISTS assets.target_credentials (
    id SERIAL PRIMARY KEY,
    target_id INTEGER NOT NULL REFERENCES assets.targets(id) ON DELETE CASCADE,
    encrypted_credentials TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure one credential set per target
    UNIQUE(target_id)
);

-- Target groups table with materialized path for efficient hierarchy queries
CREATE TABLE IF NOT EXISTS assets.target_groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    parent_group_id INTEGER REFERENCES assets.target_groups(id) ON DELETE CASCADE,
    path VARCHAR(500) NOT NULL, -- Materialized path like '/1/2/4/'
    level INTEGER CHECK (level >= 1 AND level <= 3) NOT NULL,
    color VARCHAR(7), -- Hex color like '#FF5733'
    icon VARCHAR(50), -- Icon name/class for UI
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT unique_name_per_parent UNIQUE (name, parent_group_id),
    CONSTRAINT valid_path_format CHECK (path ~ '^(/\d+)+/$')
);

-- Target group memberships (many-to-many relationship)
CREATE TABLE IF NOT EXISTS assets.target_group_memberships (
    id SERIAL PRIMARY KEY,
    target_id INTEGER REFERENCES assets.enhanced_targets(id) ON DELETE CASCADE,
    group_id INTEGER REFERENCES assets.target_groups(id) ON DELETE CASCADE,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    added_by INTEGER, -- Could reference identity.users(id) if needed
    
    -- Prevent duplicate memberships
    UNIQUE(target_id, group_id)
);

-- Service definitions table (for frontend metadata)
CREATE TABLE IF NOT EXISTS assets.service_definitions (
    id SERIAL PRIMARY KEY,
    service_type VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    default_port INTEGER NOT NULL,
    is_secure_by_default BOOLEAN DEFAULT false,
    description TEXT,
    is_common BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
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

-- Assets service indexes
CREATE INDEX IF NOT EXISTS idx_targets_host ON assets.targets(host);
CREATE INDEX IF NOT EXISTS idx_targets_type ON assets.targets(target_type);
CREATE INDEX IF NOT EXISTS idx_targets_active ON assets.targets(is_active);
CREATE INDEX IF NOT EXISTS idx_enhanced_targets_ip ON assets.enhanced_targets(ip_address);
CREATE INDEX IF NOT EXISTS idx_enhanced_targets_hostname ON assets.enhanced_targets(hostname);
CREATE INDEX IF NOT EXISTS idx_enhanced_targets_os_type ON assets.enhanced_targets(os_type);
CREATE INDEX IF NOT EXISTS idx_target_services_target_id ON assets.target_services(target_id);
CREATE INDEX IF NOT EXISTS idx_target_services_service_type ON assets.target_services(service_type);
CREATE INDEX IF NOT EXISTS idx_target_credentials_target_id ON assets.target_credentials(target_id);

-- Target groups indexes
CREATE INDEX IF NOT EXISTS idx_target_groups_path ON assets.target_groups(path);
CREATE INDEX IF NOT EXISTS idx_target_groups_parent ON assets.target_groups(parent_group_id);
CREATE INDEX IF NOT EXISTS idx_target_groups_level ON assets.target_groups(level);
CREATE INDEX IF NOT EXISTS idx_target_groups_name ON assets.target_groups(name);
CREATE INDEX IF NOT EXISTS idx_target_group_memberships_target ON assets.target_group_memberships(target_id);
CREATE INDEX IF NOT EXISTS idx_target_group_memberships_group ON assets.target_group_memberships(group_id);

-- Service definitions indexes
CREATE INDEX IF NOT EXISTS idx_service_definitions_category ON assets.service_definitions(category);
CREATE INDEX IF NOT EXISTS idx_service_definitions_common ON assets.service_definitions(is_common);

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

-- Function to automatically update path when parent changes
CREATE OR REPLACE FUNCTION assets.update_target_group_path()
RETURNS TRIGGER AS $$
DECLARE
    parent_path VARCHAR(500) := '';
    new_path VARCHAR(500);
BEGIN
    -- If this is a root group (no parent)
    IF NEW.parent_group_id IS NULL THEN
        NEW.path := '/' || NEW.id || '/';
        NEW.level := 1;
    ELSE
        -- Get parent's path and level
        SELECT path, level INTO parent_path, NEW.level 
        FROM assets.target_groups 
        WHERE id = NEW.parent_group_id;
        
        -- Increment level
        NEW.level := NEW.level + 1;
        
        -- Build new path
        NEW.path := parent_path || NEW.id || '/';
        
        -- Enforce 3-level limit
        IF NEW.level > 3 THEN
            RAISE EXCEPTION 'Target groups cannot exceed 3 levels deep';
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically maintain path and level
DROP TRIGGER IF EXISTS trigger_update_target_group_path ON assets.target_groups;
CREATE TRIGGER trigger_update_target_group_path
    BEFORE INSERT OR UPDATE OF parent_group_id ON assets.target_groups
    FOR EACH ROW
    EXECUTE FUNCTION assets.update_target_group_path();

-- Function to prevent circular references
CREATE OR REPLACE FUNCTION assets.prevent_circular_group_reference()
RETURNS TRIGGER AS $$
BEGIN
    -- Check if the new parent would create a circular reference
    IF NEW.parent_group_id IS NOT NULL THEN
        -- Check if the new parent is a descendant of this group
        IF EXISTS (
            SELECT 1 FROM assets.target_groups 
            WHERE id = NEW.parent_group_id 
            AND path LIKE (SELECT path || '%' FROM assets.target_groups WHERE id = NEW.id)
        ) THEN
            RAISE EXCEPTION 'Cannot create circular reference: group cannot be its own ancestor';
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to prevent circular references
DROP TRIGGER IF EXISTS trigger_prevent_circular_group_reference ON assets.target_groups;
CREATE TRIGGER trigger_prevent_circular_group_reference
    BEFORE UPDATE OF parent_group_id ON assets.target_groups
    FOR EACH ROW
    EXECUTE FUNCTION assets.prevent_circular_group_reference();

-- Function to update all descendant paths when a group is moved
CREATE OR REPLACE FUNCTION assets.update_descendant_paths()
RETURNS TRIGGER AS $$
DECLARE
    old_path VARCHAR(500);
    new_path VARCHAR(500);
    descendant RECORD;
BEGIN
    -- Only process if path actually changed
    IF OLD.path != NEW.path THEN
        old_path := OLD.path;
        new_path := NEW.path;
        
        -- Update all descendants
        FOR descendant IN 
            SELECT id, path FROM assets.target_groups 
            WHERE path LIKE old_path || '%' AND id != NEW.id
        LOOP
            UPDATE assets.target_groups 
            SET path = new_path || substring(descendant.path from length(old_path) + 1),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = descendant.id;
        END LOOP;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update descendant paths
DROP TRIGGER IF EXISTS trigger_update_descendant_paths ON assets.target_groups;
CREATE TRIGGER trigger_update_descendant_paths
    AFTER UPDATE OF path ON assets.target_groups
    FOR EACH ROW
    EXECUTE FUNCTION assets.update_descendant_paths();

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
  "executions:read", "users:read"
]', true),
('operator', 'System Operator', '[
  "jobs:read", "jobs:create", "jobs:update", "jobs:execute", "jobs:delete",
  "targets:read", "targets:create", "targets:update", "targets:delete",
  "executions:read"
]', true),
('developer', 'Developer', '[
  "jobs:read", "jobs:create", "jobs:update", "jobs:execute",
  "targets:read", "executions:read"
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

-- Create default target groups
INSERT INTO assets.target_groups (name, description, parent_group_id) VALUES
('Production', 'Production environment systems', NULL),
('Development', 'Development environment systems', NULL),
('Testing', 'Testing environment systems', NULL)
ON CONFLICT (name, parent_group_id) DO NOTHING;

-- Insert service definitions for frontend metadata
INSERT INTO assets.service_definitions (service_type, display_name, category, default_port, is_secure_by_default, description, is_common) VALUES
-- Remote Access
('ssh', 'SSH', 'Remote Access', 22, true, 'Secure Shell remote access', true),
('rdp', 'RDP', 'Remote Access', 3389, false, 'Remote Desktop Protocol', true),
('vnc', 'VNC', 'Remote Access', 5900, false, 'Virtual Network Computing', true),
('telnet', 'Telnet', 'Remote Access', 23, false, 'Telnet remote access (insecure)', false),

-- Windows Management
('winrm', 'WinRM HTTP', 'Windows Management', 5985, false, 'Windows Remote Management over HTTP', true),
('winrm_https', 'WinRM HTTPS', 'Windows Management', 5986, true, 'Windows Remote Management over HTTPS', true),
('wmi', 'WMI', 'Windows Management', 135, false, 'Windows Management Instrumentation', true),
('smb', 'SMB/CIFS', 'Windows Management', 445, false, 'Server Message Block file sharing', true),

-- Web Services
('http', 'HTTP', 'Web Services', 80, false, 'Hypertext Transfer Protocol', true),
('https', 'HTTPS', 'Web Services', 443, true, 'HTTP over SSL/TLS', true),
('http_alt', 'HTTP (Alt)', 'Web Services', 8080, false, 'HTTP on alternative port', true),
('https_alt', 'HTTPS (Alt)', 'Web Services', 8443, true, 'HTTPS on alternative port', true),

-- Database Services
('mysql', 'MySQL', 'Database Services', 3306, false, 'MySQL database server', true),
('postgresql', 'PostgreSQL', 'Database Services', 5432, false, 'PostgreSQL database server', true),
('sql_server', 'SQL Server', 'Database Services', 1433, false, 'Microsoft SQL Server', true),
('oracle', 'Oracle DB', 'Database Services', 1521, false, 'Oracle database server', true),
('mongodb', 'MongoDB', 'Database Services', 27017, false, 'MongoDB document database', true),
('redis', 'Redis', 'Database Services', 6379, false, 'Redis key-value store', true),

-- Email Services
('smtp', 'SMTP', 'Email Services', 25, false, 'Simple Mail Transfer Protocol', true),
('smtps', 'SMTPS', 'Email Services', 465, true, 'SMTP over SSL', true),
('smtp_submission', 'SMTP Submission', 'Email Services', 587, true, 'SMTP with STARTTLS', true),
('imap', 'IMAP', 'Email Services', 143, false, 'Internet Message Access Protocol', true),
('imaps', 'IMAPS', 'Email Services', 993, true, 'IMAP over SSL', true),
('pop3', 'POP3', 'Email Services', 110, false, 'Post Office Protocol v3', true),
('pop3s', 'POP3S', 'Email Services', 995, true, 'POP3 over SSL', true),

-- File Transfer
('ftp', 'FTP', 'File Transfer', 21, false, 'File Transfer Protocol', true),
('ftps', 'FTPS', 'File Transfer', 990, true, 'FTP over SSL', true),
('sftp', 'SFTP', 'File Transfer', 22, true, 'SSH File Transfer Protocol', true),

-- Network Services
('dns', 'DNS', 'Network Services', 53, false, 'Domain Name System', true),
('snmp', 'SNMP', 'Network Services', 161, false, 'Simple Network Management Protocol', true),
('ntp', 'NTP', 'Network Services', 123, false, 'Network Time Protocol', true)
ON CONFLICT (service_type) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    category = EXCLUDED.category,
    default_port = EXCLUDED.default_port,
    is_secure_by_default = EXCLUDED.is_secure_by_default,
    description = EXCLUDED.description,
    is_common = EXCLUDED.is_common;

COMMIT;