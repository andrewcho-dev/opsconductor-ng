-- OpsConductor Database Schema
-- Complete database schema as specified in the implementation plan
-- This creates all tables for the microservice system

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- USERS & AUTHENTICATION
CREATE TABLE IF NOT EXISTS users (
  id BIGSERIAL PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  username TEXT UNIQUE NOT NULL,
  pwd_hash TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'operator' CHECK (role IN ('admin', 'operator', 'viewer')),
  token_version INT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Create indexes for users table
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- TARGETS & CREDENTIALS
CREATE TABLE IF NOT EXISTS credentials (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  credential_type TEXT NOT NULL CHECK (credential_type IN ('winrm', 'ssh', 'api_key')),
  description TEXT,
  credential_data JSONB NOT NULL,    -- Encrypted credential data
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ
);

-- Create indexes for credentials table
CREATE INDEX IF NOT EXISTS idx_credentials_credential_type ON credentials(credential_type);
CREATE INDEX IF NOT EXISTS idx_credentials_created_at ON credentials(created_at);
CREATE INDEX IF NOT EXISTS idx_credentials_name ON credentials(name);

-- SERVICE DEFINITIONS (Master list of available service types)
CREATE TABLE IF NOT EXISTS service_definitions (
  id SERIAL PRIMARY KEY,
  service_type VARCHAR(50) UNIQUE NOT NULL,
  display_name VARCHAR(100) NOT NULL,
  category VARCHAR(50) NOT NULL,
  default_port INTEGER,
  is_secure_by_default BOOLEAN DEFAULT false,
  description TEXT,
  is_common BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for service_definitions table
CREATE INDEX IF NOT EXISTS idx_service_definitions_category ON service_definitions(category);
CREATE INDEX IF NOT EXISTS idx_service_definitions_common ON service_definitions(is_common);
CREATE INDEX IF NOT EXISTS idx_service_definitions_service_type ON service_definitions(service_type);

-- TARGETS (Enhanced - removed protocol/port, now service-independent)
CREATE TABLE IF NOT EXISTS targets (
  id BIGSERIAL PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  hostname TEXT NOT NULL,
  ip_address INET,
  os_type VARCHAR(20) CHECK (os_type IN ('windows', 'linux', 'unix', 'macos', 'other')),
  os_version TEXT,
  description TEXT,
  tags TEXT[] NOT NULL DEFAULT '{}',
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  depends_on INT[] NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ,
  
  -- Legacy columns for backward compatibility (will be deprecated)
  protocol TEXT CHECK (protocol IN ('winrm', 'ssh', 'http')),
  port INT,
  credential_ref BIGINT REFERENCES credentials(id) ON DELETE SET NULL
);

-- Create indexes for targets table
CREATE INDEX IF NOT EXISTS idx_targets_os_type ON targets(os_type);
CREATE INDEX IF NOT EXISTS idx_targets_tags_gin ON targets USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_targets_metadata_gin ON targets USING GIN(metadata);
CREATE INDEX IF NOT EXISTS idx_targets_hostname ON targets(hostname);
CREATE INDEX IF NOT EXISTS idx_targets_ip_address ON targets(ip_address);
CREATE INDEX IF NOT EXISTS idx_targets_created_at ON targets(created_at);
CREATE INDEX IF NOT EXISTS idx_targets_credential_ref ON targets(credential_ref);

-- TARGET SERVICES (Multiple services per target)
CREATE TABLE IF NOT EXISTS target_services (
  id SERIAL PRIMARY KEY,
  target_id INTEGER NOT NULL REFERENCES targets(id) ON DELETE CASCADE,
  service_type VARCHAR(50) NOT NULL REFERENCES service_definitions(service_type),
  port INTEGER NOT NULL,
  is_secure BOOLEAN DEFAULT false,
  is_enabled BOOLEAN DEFAULT true,
  is_custom_port BOOLEAN DEFAULT false,
  discovery_method VARCHAR(20) DEFAULT 'manual' CHECK (discovery_method IN ('manual', 'scan', 'import')),
  connection_status VARCHAR(20) DEFAULT 'unknown' CHECK (connection_status IN ('unknown', 'connected', 'failed', 'timeout')),
  last_checked TIMESTAMPTZ,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ,
  
  -- Ensure no duplicate service types per target
  UNIQUE(target_id, service_type)
);

-- Create indexes for target_services table
CREATE INDEX IF NOT EXISTS idx_target_services_target_id ON target_services(target_id);
CREATE INDEX IF NOT EXISTS idx_target_services_service_type ON target_services(service_type);
CREATE INDEX IF NOT EXISTS idx_target_services_enabled ON target_services(is_enabled);
CREATE INDEX IF NOT EXISTS idx_target_services_status ON target_services(connection_status);
CREATE INDEX IF NOT EXISTS idx_target_services_port ON target_services(port);

-- TARGET CREDENTIALS (Many-to-many with service specificity)
CREATE TABLE IF NOT EXISTS target_credentials (
  id SERIAL PRIMARY KEY,
  target_id INTEGER NOT NULL REFERENCES targets(id) ON DELETE CASCADE,
  credential_id INTEGER NOT NULL REFERENCES credentials(id) ON DELETE CASCADE,
  service_types TEXT[] NOT NULL DEFAULT '{}', -- Array of service types this credential applies to
  is_primary BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  
  -- Ensure no duplicate credential assignments per target
  UNIQUE(target_id, credential_id)
);

-- Create indexes for target_credentials table
CREATE INDEX IF NOT EXISTS idx_target_credentials_target_id ON target_credentials(target_id);
CREATE INDEX IF NOT EXISTS idx_target_credentials_credential_id ON target_credentials(credential_id);
CREATE INDEX IF NOT EXISTS idx_target_credentials_service_types_gin ON target_credentials USING GIN(service_types);
CREATE INDEX IF NOT EXISTS idx_target_credentials_primary ON target_credentials(is_primary);

-- JOBS & SCHEDULES
CREATE TABLE IF NOT EXISTS jobs (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  version INT NOT NULL DEFAULT 1,
  definition JSONB NOT NULL,
  created_by BIGINT REFERENCES users(id),
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Create indexes for jobs table
CREATE INDEX IF NOT EXISTS idx_jobs_name ON jobs(name);
CREATE INDEX IF NOT EXISTS idx_jobs_created_by ON jobs(created_by);
CREATE INDEX IF NOT EXISTS idx_jobs_is_active ON jobs(is_active);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at);

CREATE TABLE IF NOT EXISTS schedules (
  id BIGSERIAL PRIMARY KEY,
  job_id BIGINT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  cron TEXT NOT NULL,
  timezone TEXT NOT NULL DEFAULT 'America/Los_Angeles',
  next_run_at TIMESTAMPTZ,
  last_run_at TIMESTAMPTZ,
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Create indexes for schedules table
CREATE INDEX IF NOT EXISTS idx_schedules_job_id ON schedules(job_id);
CREATE INDEX IF NOT EXISTS idx_schedules_next_run_at ON schedules(next_run_at);
CREATE INDEX IF NOT EXISTS idx_schedules_is_active ON schedules(is_active);

-- RUNS & STEPS
CREATE TABLE IF NOT EXISTS job_runs (
  id BIGSERIAL PRIMARY KEY,
  job_id BIGINT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  status TEXT NOT NULL CHECK (status IN ('queued','running','succeeded','failed','canceled')),
  requested_by BIGINT REFERENCES users(id),
  parameters JSONB NOT NULL DEFAULT '{}'::jsonb,
  queued_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  started_at TIMESTAMPTZ,
  finished_at TIMESTAMPTZ,
  correlation_id TEXT,
  idempotency_key TEXT
);

-- Create indexes for job_runs table
CREATE INDEX IF NOT EXISTS idx_job_runs_status ON job_runs(status);
CREATE INDEX IF NOT EXISTS idx_job_runs_job ON job_runs(job_id);
CREATE INDEX IF NOT EXISTS idx_job_runs_requested_by ON job_runs(requested_by);
CREATE INDEX IF NOT EXISTS idx_job_runs_queued_at ON job_runs(queued_at);
CREATE INDEX IF NOT EXISTS idx_job_runs_correlation_id ON job_runs(correlation_id);

CREATE TABLE IF NOT EXISTS job_run_steps (
  id BIGSERIAL PRIMARY KEY,
  job_run_id BIGINT NOT NULL REFERENCES job_runs(id) ON DELETE CASCADE,
  idx INT NOT NULL,                                -- 0..N
  type TEXT NOT NULL,                              -- 'winrm.exec' | 'winrm.copy' | ...
  target_id BIGINT REFERENCES targets(id),
  status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued','running','succeeded','failed','aborted')),
  shell TEXT,                                      -- 'powershell' | 'cmd' (for exec)
  timeoutsec INT DEFAULT 60,
  exit_code INT,
  stdout TEXT,
  stderr TEXT,
  metrics JSONB,
  artifacts JSONB,
  started_at TIMESTAMPTZ,
  finished_at TIMESTAMPTZ
);

-- Create indexes for job_run_steps table
CREATE INDEX IF NOT EXISTS idx_steps_run ON job_run_steps(job_run_id);
CREATE INDEX IF NOT EXISTS idx_steps_status ON job_run_steps(status);
CREATE INDEX IF NOT EXISTS idx_steps_target_id ON job_run_steps(target_id);
CREATE INDEX IF NOT EXISTS idx_steps_type ON job_run_steps(type);
-- Full-text search index on stdout for quick searches
CREATE INDEX IF NOT EXISTS idx_steps_stdout_fts ON job_run_steps USING GIN (to_tsvector('english', coalesce(stdout,'')));

-- AUDIT & NOTIFICATIONS
CREATE TABLE IF NOT EXISTS audit_log (
  id BIGSERIAL PRIMARY KEY,
  ts TIMESTAMPTZ NOT NULL DEFAULT now(),
  actor_id BIGINT REFERENCES users(id),
  action TEXT NOT NULL,                 -- e.g., 'targets.create'
  resource_type TEXT NOT NULL,
  resource_id BIGINT,
  ip TEXT,
  user_agent TEXT,
  details JSONB,
  prev_hash BYTEA,                      -- for hash chaining (tamper-evidence)
  record_hash BYTEA NOT NULL
);

-- Create indexes for audit_log table
CREATE INDEX IF NOT EXISTS idx_audit_log_ts ON audit_log(ts);
CREATE INDEX IF NOT EXISTS idx_audit_log_actor_id ON audit_log(actor_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_log_resource_type ON audit_log(resource_type);
CREATE INDEX IF NOT EXISTS idx_audit_log_resource_id ON audit_log(resource_id);

CREATE TABLE IF NOT EXISTS notifications (
  id BIGSERIAL PRIMARY KEY,
  job_run_id BIGINT REFERENCES job_runs(id) ON DELETE CASCADE,
  channel TEXT NOT NULL CHECK (channel IN ('webhook', 'email')),
  dest TEXT NOT NULL,
  payload JSONB NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'failed')),
  sent_at TIMESTAMPTZ,
  retries INT NOT NULL DEFAULT 0
);

-- Create indexes for notifications table
CREATE INDEX IF NOT EXISTS idx_notifications_job_run_id ON notifications(job_run_id);
CREATE INDEX IF NOT EXISTS idx_notifications_status ON notifications(status);
CREATE INDEX IF NOT EXISTS idx_notifications_channel ON notifications(channel);

-- DLQ for failed dispatches/processing (optional but recommended)
CREATE TABLE IF NOT EXISTS dlq (
  id BIGSERIAL PRIMARY KEY,
  topic TEXT NOT NULL,
  payload JSONB NOT NULL,
  error TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Create indexes for dlq table
CREATE INDEX IF NOT EXISTS idx_dlq_topic ON dlq(topic);
CREATE INDEX IF NOT EXISTS idx_dlq_created_at ON dlq(created_at);

-- Insert initial data for testing and development
-- Default admin user (password: admin123 - change in production!)
INSERT INTO users (email, username, pwd_hash, role, created_at) VALUES 
('admin@opsconductor.local', 'admin', '$2b$10$a2WMKfX7C07fLuG1KpFivu4tNGT07TDmHDbogVx26cB3Ds0WDsDlS', 'admin', NOW()),
('operator@opsconductor.local', 'operator', '$2b$10$a2WMKfX7C07fLuG1KpFivu4tNGT07TDmHDbogVx26cB3Ds0WDsDlS', 'operator', NOW()),
('viewer@opsconductor.local', 'viewer', '$2b$10$a2WMKfX7C07fLuG1KpFivu4tNGT07TDmHDbogVx26cB3Ds0WDsDlS', 'viewer', NOW())
ON CONFLICT (email) DO NOTHING;

-- Sample credentials (encrypted data will be managed by the credentials service)
INSERT INTO credentials (name, credential_type, description, credential_data, created_at) VALUES 
('sample-winrm-admin', 'winrm', 'Sample Windows admin credentials', '{"encrypted": true, "data": ""}', NOW()),
('sample-ssh-key', 'ssh', 'Sample SSH key credentials', '{"encrypted": true, "data": ""}', NOW())
ON CONFLICT (name) DO NOTHING;

-- Insert comprehensive service definitions
INSERT INTO service_definitions (service_type, display_name, category, default_port, is_secure_by_default, description, is_common) VALUES 
-- Remote Management & Execution (Most Common)
('ssh', 'SSH (Secure Shell)', 'remote', 22, true, 'Secure Shell for Linux/Unix systems', true),
('winrm', 'WinRM HTTP', 'remote', 5985, false, 'Windows Remote Management over HTTP', true),
('winrm_https', 'WinRM HTTPS', 'remote', 5986, true, 'Windows Remote Management over HTTPS', true),
('rdp', 'Remote Desktop Protocol', 'remote', 3389, false, 'Windows Remote Desktop Protocol', true),
('vnc', 'VNC', 'remote', 5900, false, 'Virtual Network Computing', false),
('telnet', 'Telnet', 'remote', 23, false, 'Telnet Protocol (Legacy)', false),

-- Web Services
('http', 'HTTP', 'web', 80, false, 'HTTP Web Service', true),
('https', 'HTTPS', 'web', 443, true, 'HTTPS Secure Web Service', true),
('http_alt', 'HTTP Alternative', 'web', 8080, false, 'Alternative HTTP port', false),
('https_alt', 'HTTPS Alternative', 'web', 8443, true, 'Alternative HTTPS port', false),
('http_proxy', 'HTTP Proxy', 'web', 3128, false, 'HTTP Proxy Service', false),
('socks', 'SOCKS Proxy', 'web', 1080, false, 'SOCKS Proxy Service', false),

-- File Transfer & Sharing
('ftp', 'FTP', 'file', 21, false, 'File Transfer Protocol', true),
('ftps', 'FTPS', 'file', 990, true, 'FTP over SSL/TLS', false),
('sftp', 'SFTP', 'file', 22, true, 'SSH File Transfer Protocol', true),
('smb', 'SMB/CIFS', 'file', 445, false, 'Server Message Block', true),
('nfs', 'NFS', 'file', 2049, false, 'Network File System', false),
('rsync', 'Rsync', 'file', 873, false, 'Remote Sync Protocol', false),

-- Database Services
('mysql', 'MySQL', 'database', 3306, false, 'MySQL Database', true),
('postgresql', 'PostgreSQL', 'database', 5432, false, 'PostgreSQL Database', true),
('sql_server', 'Microsoft SQL Server', 'database', 1433, false, 'Microsoft SQL Server', true),
('oracle', 'Oracle Database', 'database', 1521, false, 'Oracle Database', false),
('mongodb', 'MongoDB', 'database', 27017, false, 'MongoDB Database', true),
('redis', 'Redis', 'database', 6379, false, 'Redis In-Memory Database', true),
('elasticsearch', 'Elasticsearch', 'database', 9200, false, 'Elasticsearch Search Engine', false),
('cassandra', 'Cassandra', 'database', 9042, false, 'Apache Cassandra', false),

-- Network Management
('snmp', 'SNMP', 'network', 161, false, 'Simple Network Management Protocol', true),
('snmp_trap', 'SNMP Trap', 'network', 162, false, 'SNMP Trap Receiver', false),
('wmi', 'WMI', 'network', 135, false, 'Windows Management Instrumentation', true),
('netbios', 'NetBIOS', 'network', 139, false, 'NetBIOS Session Service', false),
('dns', 'DNS', 'network', 53, false, 'Domain Name System', true),
('dhcp', 'DHCP Server', 'network', 67, false, 'DHCP Server', false),
('dhcp_client', 'DHCP Client', 'network', 68, false, 'DHCP Client', false),
('ntp', 'NTP', 'network', 123, false, 'Network Time Protocol', true),

-- Directory & Authentication
('ldap', 'LDAP', 'directory', 389, false, 'Lightweight Directory Access Protocol', true),
('ldaps', 'LDAPS', 'directory', 636, true, 'LDAP over SSL', true),
('kerberos', 'Kerberos', 'directory', 88, false, 'Kerberos Authentication', false),
('radius', 'RADIUS', 'directory', 1812, false, 'Remote Authentication Dial-In User Service', false),

-- Email Services
('smtp', 'SMTP', 'email', 25, false, 'Simple Mail Transfer Protocol', true),
('smtp_submission', 'SMTP Submission', 'email', 587, true, 'SMTP Mail Submission', true),
('smtps', 'SMTPS', 'email', 465, true, 'SMTP over SSL', true),
('pop3', 'POP3', 'email', 110, false, 'Post Office Protocol v3', false),
('pop3s', 'POP3S', 'email', 995, true, 'POP3 over SSL', false),
('imap', 'IMAP', 'email', 143, false, 'Internet Message Access Protocol', true),
('imaps', 'IMAPS', 'email', 993, true, 'IMAP over SSL', true),

-- Application & Monitoring
('docker', 'Docker API', 'application', 2376, true, 'Docker Remote API', true),
('kubernetes', 'Kubernetes API', 'application', 6443, true, 'Kubernetes API Server', true),
('prometheus', 'Prometheus', 'monitoring', 9090, false, 'Prometheus Monitoring', true),
('grafana', 'Grafana', 'monitoring', 3000, false, 'Grafana Dashboard', true),
('jenkins', 'Jenkins', 'application', 8080, false, 'Jenkins CI/CD', true),
('nagios', 'Nagios', 'monitoring', 5666, false, 'Nagios Remote Plugin Executor', false),
('zabbix', 'Zabbix Agent', 'monitoring', 10050, false, 'Zabbix Monitoring Agent', false),

-- Virtualization & Cloud
('vmware_esxi', 'VMware ESXi', 'virtualization', 443, true, 'VMware ESXi Management', false),
('hyper_v', 'Hyper-V', 'virtualization', 2179, false, 'Microsoft Hyper-V', false),
('aws_ssm', 'AWS SSM', 'cloud', 443, true, 'AWS Systems Manager', false),
('azure_arc', 'Azure Arc', 'cloud', 443, true, 'Azure Arc Agent', false)
ON CONFLICT (service_type) DO NOTHING;

-- Sample targets (updated for new schema)
INSERT INTO targets (name, hostname, ip_address, os_type, os_version, description, tags, metadata, depends_on, created_at) VALUES 
('sample-windows-server', 'win-server-01.example.com', '192.168.1.100', 'windows', 'Windows Server 2019', 'Sample Windows server for development', ARRAY['environment:dev', 'role:web-server'], '{"domain": "EXAMPLE"}', ARRAY[]::int[], NOW()),
('sample-linux-server', 'linux-server-01.example.com', '192.168.1.101', 'linux', 'Ubuntu 20.04', 'Sample Linux server for development', ARRAY['environment:dev', 'role:database'], '{}', ARRAY[]::int[], NOW())
ON CONFLICT (name) DO NOTHING;

-- Sample target services (assign services to sample targets)
INSERT INTO target_services (target_id, service_type, port, is_secure, is_enabled, is_custom_port, discovery_method) VALUES 
-- Windows server services
(1, 'winrm_https', 5986, true, true, false, 'manual'),
(1, 'rdp', 3389, false, true, false, 'manual'),
(1, 'http', 80, false, true, false, 'manual'),
(1, 'https', 443, true, true, false, 'manual'),
(1, 'smb', 445, false, true, false, 'manual'),
-- Linux server services  
(2, 'ssh', 22, true, true, false, 'manual'),
(2, 'http', 80, false, true, false, 'manual'),
(2, 'mysql', 3306, false, true, false, 'manual'),
(2, 'snmp', 161, false, false, false, 'manual')
ON CONFLICT (target_id, service_type) DO NOTHING;

-- Sample target credentials (assign credentials to targets for specific services)
INSERT INTO target_credentials (target_id, credential_id, service_types, is_primary) VALUES 
(1, 1, ARRAY['winrm_https', 'rdp'], true),  -- Windows admin creds for WinRM and RDP
(2, 2, ARRAY['ssh'], true)                  -- SSH key for Linux server
ON CONFLICT (target_id, credential_id) DO NOTHING;

-- Sample job definition
INSERT INTO jobs (name, version, definition, created_by, is_active, created_at) VALUES 
('Sample Windows Service Restart', 1, 
'{"name": "Restart service on Windows", "version": 1, "parameters": {"svc": "Spooler"}, "steps": [{"type": "winrm.exec", "shell": "powershell", "target": "sample-windows-server", "command": "Restart-Service {{ svc }}; (Get-Service {{ svc }}).Status", "timeoutSec": 90}]}', 
1, true, NOW())
ON CONFLICT DO NOTHING;

-- MIGRATION FUNCTION: Convert legacy single-service targets to multi-service
CREATE OR REPLACE FUNCTION migrate_old_targets_to_new_schema()
RETURNS TEXT AS $$
DECLARE
    target_record RECORD;
    service_count INTEGER := 0;
    credential_count INTEGER := 0;
    result_text TEXT := '';
BEGIN
    -- Migrate existing targets with legacy protocol/port to new service structure
    FOR target_record IN 
        SELECT id, name, protocol, port, credential_ref 
        FROM targets 
        WHERE protocol IS NOT NULL AND port IS NOT NULL
    LOOP
        -- Create target service based on legacy protocol
        INSERT INTO target_services (target_id, service_type, port, is_secure, is_enabled, is_custom_port, discovery_method)
        VALUES (
            target_record.id,
            target_record.protocol,
            target_record.port,
            CASE 
                WHEN target_record.protocol = 'winrm_https' OR target_record.protocol = 'ssh' THEN true
                ELSE false
            END,
            true,
            CASE 
                WHEN (target_record.protocol = 'winrm' AND target_record.port != 5985) OR
                     (target_record.protocol = 'winrm_https' AND target_record.port != 5986) OR
                     (target_record.protocol = 'ssh' AND target_record.port != 22) OR
                     (target_record.protocol = 'http' AND target_record.port != 80)
                THEN true
                ELSE false
            END,
            'manual'
        )
        ON CONFLICT (target_id, service_type) DO NOTHING;
        
        service_count := service_count + 1;
        
        -- Create target credential mapping if credential exists
        IF target_record.credential_ref IS NOT NULL THEN
            INSERT INTO target_credentials (target_id, credential_id, service_types, is_primary)
            VALUES (
                target_record.id,
                target_record.credential_ref,
                ARRAY[target_record.protocol],
                true
            )
            ON CONFLICT (target_id, credential_id) DO NOTHING;
            
            credential_count := credential_count + 1;
        END IF;
    END LOOP;
    
    result_text := format('Migration completed: %s services created, %s credential mappings created', 
                         service_count, credential_count);
    
    RETURN result_text;
END;
$$ LANGUAGE plpgsql;

-- UTILITY FUNCTIONS for multi-service management

-- Function to get all services for a target
CREATE OR REPLACE FUNCTION get_target_services(target_id_param INTEGER)
RETURNS TABLE (
    service_id INTEGER,
    service_type VARCHAR(50),
    display_name VARCHAR(100),
    category VARCHAR(50),
    port INTEGER,
    default_port INTEGER,
    is_secure BOOLEAN,
    is_enabled BOOLEAN,
    is_custom_port BOOLEAN,
    connection_status VARCHAR(20),
    last_checked TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ts.id,
        ts.service_type,
        sd.display_name,
        sd.category,
        ts.port,
        sd.default_port,
        ts.is_secure,
        ts.is_enabled,
        ts.is_custom_port,
        ts.connection_status,
        ts.last_checked
    FROM target_services ts
    JOIN service_definitions sd ON ts.service_type = sd.service_type
    WHERE ts.target_id = target_id_param
    ORDER BY sd.category, sd.display_name;
END;
$$ LANGUAGE plpgsql;

-- Function to get credentials for a target's services
CREATE OR REPLACE FUNCTION get_target_credentials(target_id_param INTEGER)
RETURNS TABLE (
    credential_id INTEGER,
    credential_name TEXT,
    credential_type TEXT,
    service_types TEXT[],
    is_primary BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.id,
        c.name,
        c.credential_type,
        tc.service_types,
        tc.is_primary
    FROM target_credentials tc
    JOIN credentials c ON tc.credential_id = c.id
    WHERE tc.target_id = target_id_param
    ORDER BY tc.is_primary DESC, c.name;
END;
$$ LANGUAGE plpgsql;

-- Create a view for easier job run monitoring
CREATE OR REPLACE VIEW job_run_summary AS
SELECT 
    jr.id as run_id,
    j.name as job_name,
    jr.status as run_status,
    jr.queued_at,
    jr.started_at,
    jr.finished_at,
    jr.requested_by,
    u.username as requested_by_username,
    COUNT(jrs.id) as total_steps,
    COUNT(CASE WHEN jrs.status = 'succeeded' THEN 1 END) as succeeded_steps,
    COUNT(CASE WHEN jrs.status = 'failed' THEN 1 END) as failed_steps,
    COUNT(CASE WHEN jrs.status = 'running' THEN 1 END) as running_steps
FROM job_runs jr
JOIN jobs j ON jr.job_id = j.id
LEFT JOIN users u ON jr.requested_by = u.id
LEFT JOIN job_run_steps jrs ON jr.id = jrs.job_run_id
GROUP BY jr.id, j.name, jr.status, jr.queued_at, jr.started_at, jr.finished_at, jr.requested_by, u.username;

-- Grant permissions (adjust based on your database setup)
-- These would be uncommented and customized for production
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO opsconductor_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO opsconductor_app;

-- Add comments for documentation
COMMENT ON TABLE users IS 'User accounts with role-based access control';
COMMENT ON TABLE credentials IS 'Encrypted credential storage with AES-GCM envelope encryption';
COMMENT ON TABLE targets IS 'Target systems for job execution (Windows/Linux)';
COMMENT ON TABLE jobs IS 'Job definitions with JSON-based step configuration';
COMMENT ON TABLE schedules IS 'Cron-based job scheduling';
COMMENT ON TABLE job_runs IS 'Job execution instances with status tracking';
COMMENT ON TABLE job_run_steps IS 'Individual step execution within job runs';
COMMENT ON TABLE audit_log IS 'Audit trail with hash chaining for tamper evidence';
COMMENT ON TABLE notifications IS 'Notification delivery tracking (email/webhook)';
COMMENT ON TABLE dlq IS 'Dead letter queue for failed message processing';

-- =============================================================================
-- STEP LIBRARIES SYSTEM TABLES
-- =============================================================================

-- STEP LIBRARIES TABLE
-- Stores metadata and information about installed step libraries
CREATE TABLE IF NOT EXISTS step_libraries (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,                    -- Library identifier (e.g., 'file-operations')
    version VARCHAR(20) NOT NULL,                  -- Semantic version (e.g., '1.2.3')
    display_name VARCHAR(200) NOT NULL,            -- Human-readable name
    description TEXT,                              -- Library description
    author VARCHAR(100) NOT NULL,                  -- Library author
    author_email VARCHAR(255),                     -- Author contact email
    homepage TEXT,                                 -- Library homepage URL
    repository TEXT,                               -- Source repository URL
    license VARCHAR(50) DEFAULT 'MIT',             -- License type
    categories TEXT[] DEFAULT '{}',                -- Library categories
    tags TEXT[] DEFAULT '{}',                      -- Search tags
    dependencies TEXT[] DEFAULT '{}',              -- Required dependencies
    min_opsconductor_version VARCHAR(20) DEFAULT '1.0.0', -- Minimum OpsConductor version
    
    -- Premium/Commercial Support
    is_premium BOOLEAN DEFAULT false,              -- Whether library requires premium license
    price DECIMAL(10,2),                          -- Library price (if premium)
    trial_days INTEGER,                           -- Trial period in days
    license_key_hash VARCHAR(255),                -- Hashed license key for validation
    
    -- Installation & Status
    file_path TEXT NOT NULL,                      -- Path to library files
    file_hash VARCHAR(64) NOT NULL,               -- SHA-256 hash of library file
    file_size BIGINT,                            -- File size in bytes
    is_enabled BOOLEAN DEFAULT true,              -- Whether library is active
    installation_date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMPTZ,                     -- Last update timestamp
    last_used TIMESTAMPTZ,                       -- Last time library was used
    usage_count INTEGER DEFAULT 0,               -- Number of times library steps were executed
    
    -- Status and Health
    status VARCHAR(20) DEFAULT 'installed' CHECK (status IN ('installed', 'enabled', 'disabled', 'error', 'updating', 'deprecated')),
    error_message TEXT,                          -- Error details if status is 'error'
    health_check_date TIMESTAMPTZ,              -- Last health check
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE(name, version),                       -- Prevent duplicate library versions
    CHECK (version ~ '^[0-9]+\.[0-9]+\.[0-9]+'), -- Semantic versioning validation
    CHECK (is_premium = false OR (is_premium = true AND price > 0)) -- Premium libraries must have price
);

-- LIBRARY STEPS TABLE
-- Stores individual step definitions within libraries
CREATE TABLE IF NOT EXISTS library_steps (
    id SERIAL PRIMARY KEY,
    library_id INTEGER NOT NULL REFERENCES step_libraries(id) ON DELETE CASCADE,
    
    -- Step Identity
    name VARCHAR(100) NOT NULL,                   -- Step identifier (e.g., 'file.create')
    display_name VARCHAR(200) NOT NULL,           -- Human-readable step name
    category VARCHAR(50) NOT NULL,                -- Step category (file, network, logic, etc.)
    description TEXT,                             -- Step description
    
    -- Visual Properties
    icon VARCHAR(10) DEFAULT '📄',                -- Step icon (emoji or icon class)
    color VARCHAR(7) DEFAULT '#007bff',           -- Step color (hex)
    
    -- Flow Properties
    inputs INTEGER DEFAULT 1,                     -- Number of input ports
    outputs INTEGER DEFAULT 1,                    -- Number of output ports
    
    -- Configuration
    parameters JSONB DEFAULT '{}',                -- Step parameters schema
    platform_support TEXT[] DEFAULT ARRAY['windows', 'linux', 'macos'], -- Supported platforms
    required_permissions TEXT[] DEFAULT '{}',     -- Required permissions
    examples JSONB DEFAULT '[]',                  -- Usage examples
    tags TEXT[] DEFAULT '{}',                     -- Search tags
    
    -- Performance & Usage
    execution_count INTEGER DEFAULT 0,            -- Number of times step was executed
    avg_execution_time_ms INTEGER,               -- Average execution time
    last_executed TIMESTAMPTZ,                   -- Last execution timestamp
    
    -- Status
    is_deprecated BOOLEAN DEFAULT false,          -- Whether step is deprecated
    deprecation_message TEXT,                    -- Deprecation notice
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE(library_id, name),                    -- Prevent duplicate steps within library
    CHECK (inputs >= 0 AND inputs <= 10),       -- Reasonable input port limits
    CHECK (outputs >= 0 AND outputs <= 10),     -- Reasonable output port limits
    CHECK (color ~ '^#[0-9A-Fa-f]{6}$')        -- Valid hex color
);

-- LIBRARY USAGE ANALYTICS TABLE
-- Tracks library and step usage for analytics and optimization
CREATE TABLE IF NOT EXISTS library_usage_analytics (
    id SERIAL PRIMARY KEY,
    library_id INTEGER REFERENCES step_libraries(id) ON DELETE CASCADE,
    step_id INTEGER REFERENCES library_steps(id) ON DELETE CASCADE,
    
    -- Usage Context
    user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    job_run_id BIGINT REFERENCES job_runs(id) ON DELETE SET NULL,
    
    -- Execution Details
    execution_time_ms INTEGER,                   -- Execution time in milliseconds
    memory_usage_mb INTEGER,                     -- Memory usage in MB
    success BOOLEAN,                             -- Whether execution was successful
    error_message TEXT,                          -- Error details if failed
    
    -- Metadata
    executed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    platform VARCHAR(20),                        -- Execution platform
    opsconductor_version VARCHAR(20),            -- OpsConductor version
    
    CHECK (execution_time_ms >= 0),
    CHECK (memory_usage_mb >= 0)
);

-- =============================================================================
-- STEP LIBRARIES INDEXES
-- =============================================================================

-- Step Libraries Indexes
CREATE INDEX IF NOT EXISTS idx_step_libraries_name ON step_libraries(name);
CREATE INDEX IF NOT EXISTS idx_step_libraries_enabled ON step_libraries(is_enabled);
CREATE INDEX IF NOT EXISTS idx_step_libraries_premium ON step_libraries(is_premium);
CREATE INDEX IF NOT EXISTS idx_step_libraries_status ON step_libraries(status);
CREATE INDEX IF NOT EXISTS idx_step_libraries_categories_gin ON step_libraries USING GIN(categories);
CREATE INDEX IF NOT EXISTS idx_step_libraries_tags_gin ON step_libraries USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_step_libraries_installation_date ON step_libraries(installation_date);
CREATE INDEX IF NOT EXISTS idx_step_libraries_last_used ON step_libraries(last_used);

-- Library Steps Indexes
CREATE INDEX IF NOT EXISTS idx_library_steps_library_id ON library_steps(library_id);
CREATE INDEX IF NOT EXISTS idx_library_steps_category ON library_steps(category);
CREATE INDEX IF NOT EXISTS idx_library_steps_name ON library_steps(name);
CREATE INDEX IF NOT EXISTS idx_library_steps_platform_gin ON library_steps USING GIN(platform_support);
CREATE INDEX IF NOT EXISTS idx_library_steps_tags_gin ON library_steps USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_library_steps_deprecated ON library_steps(is_deprecated);

-- Usage Analytics Indexes
CREATE INDEX IF NOT EXISTS idx_usage_analytics_library_id ON library_usage_analytics(library_id);
CREATE INDEX IF NOT EXISTS idx_usage_analytics_step_id ON library_usage_analytics(step_id);
CREATE INDEX IF NOT EXISTS idx_usage_analytics_executed_at ON library_usage_analytics(executed_at);
CREATE INDEX IF NOT EXISTS idx_usage_analytics_user_id ON library_usage_analytics(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_analytics_success ON library_usage_analytics(success);

-- =============================================================================
-- STEP LIBRARIES TRIGGERS
-- =============================================================================

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_step_libraries_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at columns
CREATE TRIGGER update_step_libraries_updated_at 
    BEFORE UPDATE ON step_libraries 
    FOR EACH ROW EXECUTE FUNCTION update_step_libraries_updated_at();

CREATE TRIGGER update_library_steps_updated_at 
    BEFORE UPDATE ON library_steps 
    FOR EACH ROW EXECUTE FUNCTION update_step_libraries_updated_at();

-- Function to increment usage counters
CREATE OR REPLACE FUNCTION increment_step_usage()
RETURNS TRIGGER AS $$
BEGIN
    -- Update step execution count
    UPDATE library_steps 
    SET execution_count = execution_count + 1,
        last_executed = CURRENT_TIMESTAMP
    WHERE id = NEW.step_id;
    
    -- Update library usage count
    UPDATE step_libraries 
    SET usage_count = usage_count + 1,
        last_used = CURRENT_TIMESTAMP
    WHERE id = (SELECT library_id FROM library_steps WHERE id = NEW.step_id);
    
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update usage counters
CREATE TRIGGER increment_usage_on_analytics_insert
    AFTER INSERT ON library_usage_analytics
    FOR EACH ROW EXECUTE FUNCTION increment_step_usage();

-- =============================================================================
-- STEP LIBRARIES INITIAL DATA
-- =============================================================================

-- Insert core system library (built-in steps)
INSERT INTO step_libraries (
    name, version, display_name, description, author, 
    file_path, file_hash, is_enabled, status
) VALUES (
    'core', '1.0.0', 'Core System Library', 
    'Built-in core steps for flow control and basic operations',
    'OpsConductor Team', '/app/core', 'builtin', true, 'installed'
) ON CONFLICT (name, version) DO NOTHING;

-- Performance optimization: Analyze tables after initial data load
ANALYZE;