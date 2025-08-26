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

CREATE TABLE IF NOT EXISTS targets (
  id BIGSERIAL PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  protocol TEXT NOT NULL DEFAULT 'winrm' CHECK (protocol IN ('winrm', 'ssh', 'http')),
  hostname TEXT NOT NULL,
  port INT NOT NULL DEFAULT 5985,
  credential_ref BIGINT NOT NULL REFERENCES credentials(id) ON DELETE RESTRICT,
  tags TEXT[] NOT NULL DEFAULT '{}',
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  depends_on INT[] NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Create indexes for targets table
CREATE INDEX IF NOT EXISTS idx_targets_protocol ON targets(protocol);
CREATE INDEX IF NOT EXISTS idx_targets_tags_gin ON targets USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_targets_metadata_gin ON targets USING GIN(metadata);
CREATE INDEX IF NOT EXISTS idx_targets_hostname ON targets(hostname);
CREATE INDEX IF NOT EXISTS idx_targets_created_at ON targets(created_at);
CREATE INDEX IF NOT EXISTS idx_targets_credential_ref ON targets(credential_ref);

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

-- Sample targets
INSERT INTO targets (name, protocol, hostname, port, credential_ref, tags, metadata, depends_on, created_at) VALUES 
('sample-windows-server', 'winrm', 'win-server-01.example.com', 5986, 1, ARRAY['environment:dev', 'role:web-server'], '{"domain": "EXAMPLE"}', ARRAY[]::int[], NOW()),
('sample-linux-server', 'ssh', 'linux-server-01.example.com', 22, 2, ARRAY['environment:dev', 'role:database'], '{}', ARRAY[]::int[], NOW())
ON CONFLICT (name) DO NOTHING;

-- Sample job definition
INSERT INTO jobs (name, version, definition, created_by, is_active, created_at) VALUES 
('Sample Windows Service Restart', 1, 
'{"name": "Restart service on Windows", "version": 1, "parameters": {"svc": "Spooler"}, "steps": [{"type": "winrm.exec", "shell": "powershell", "target": "sample-windows-server", "command": "Restart-Service {{ svc }}; (Get-Service {{ svc }}).Status", "timeoutSec": 90}]}', 
1, true, NOW())
ON CONFLICT DO NOTHING;

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

-- Performance optimization: Analyze tables after initial data load
ANALYZE;