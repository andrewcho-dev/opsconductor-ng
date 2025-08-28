-- Phase 8.1: SSH/Linux Support Database Schema
-- Enhanced SSH key credentials and Linux target support

-- Add SSH key support to credential types
INSERT INTO credential_types (name, description, fields_schema) VALUES 
('ssh_key', 'SSH Private Key Authentication', '{
  "private_key": {"type": "encrypted_text", "required": true, "description": "SSH private key (PEM format)"},
  "public_key": {"type": "text", "required": false, "description": "SSH public key (optional)"},
  "passphrase": {"type": "encrypted_string", "required": false, "description": "Private key passphrase"},
  "username": {"type": "string", "required": true, "description": "SSH username"},
  "key_type": {"type": "enum", "values": ["rsa", "ed25519", "ecdsa", "dsa"], "default": "rsa", "description": "SSH key type"}
}')
ON CONFLICT (name) DO UPDATE SET
  description = EXCLUDED.description,
  fields_schema = EXCLUDED.fields_schema;

-- Add enhanced SSH password credentials
INSERT INTO credential_types (name, description, fields_schema) VALUES 
('ssh_password', 'SSH Password Authentication', '{
  "username": {"type": "string", "required": true, "description": "SSH username"},
  "password": {"type": "encrypted_string", "required": true, "description": "SSH password"},
  "port": {"type": "integer", "default": 22, "description": "SSH port"},
  "timeout": {"type": "integer", "default": 30, "description": "Connection timeout in seconds"}
}')
ON CONFLICT (name) DO UPDATE SET
  description = EXCLUDED.description,
  fields_schema = EXCLUDED.fields_schema;

-- Create SSH connection tracking table
CREATE TABLE IF NOT EXISTS ssh_connections (
    id SERIAL PRIMARY KEY,
    target_id INTEGER REFERENCES targets(id) ON DELETE CASCADE,
    credential_id INTEGER REFERENCES credentials(id) ON DELETE CASCADE,
    connection_type VARCHAR(20) NOT NULL CHECK (connection_type IN ('ssh', 'sftp')),
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'connected', 'failed', 'disconnected')),
    host VARCHAR(255) NOT NULL,
    port INTEGER NOT NULL DEFAULT 22,
    username VARCHAR(100) NOT NULL,
    auth_method VARCHAR(20) NOT NULL CHECK (auth_method IN ('password', 'key')),
    connection_info JSONB,
    last_connected_at TIMESTAMP,
    last_error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for SSH connections
CREATE INDEX IF NOT EXISTS idx_ssh_connections_target_id ON ssh_connections(target_id);
CREATE INDEX IF NOT EXISTS idx_ssh_connections_credential_id ON ssh_connections(credential_id);
CREATE INDEX IF NOT EXISTS idx_ssh_connections_status ON ssh_connections(status);
CREATE INDEX IF NOT EXISTS idx_ssh_connections_connection_type ON ssh_connections(connection_type);

-- Create SSH execution tracking table
CREATE TABLE IF NOT EXISTS ssh_executions (
    id SERIAL PRIMARY KEY,
    job_run_step_id INTEGER REFERENCES job_run_steps(id) ON DELETE CASCADE,
    target_id INTEGER REFERENCES targets(id) ON DELETE CASCADE,
    command TEXT NOT NULL,
    shell VARCHAR(20) DEFAULT 'bash' CHECK (shell IN ('bash', 'sh', 'zsh', 'fish', 'csh', 'tcsh')),
    working_directory VARCHAR(500),
    environment_vars JSONB,
    exit_code INTEGER,
    stdout TEXT,
    stderr TEXT,
    execution_time_ms INTEGER,
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for SSH executions
CREATE INDEX IF NOT EXISTS idx_ssh_executions_job_run_step_id ON ssh_executions(job_run_step_id);
CREATE INDEX IF NOT EXISTS idx_ssh_executions_target_id ON ssh_executions(target_id);
CREATE INDEX IF NOT EXISTS idx_ssh_executions_started_at ON ssh_executions(started_at);

-- Create SFTP operations tracking table
CREATE TABLE IF NOT EXISTS sftp_operations (
    id SERIAL PRIMARY KEY,
    job_run_step_id INTEGER REFERENCES job_run_steps(id) ON DELETE CASCADE,
    target_id INTEGER REFERENCES targets(id) ON DELETE CASCADE,
    operation_type VARCHAR(20) NOT NULL CHECK (operation_type IN ('upload', 'download', 'sync', 'delete', 'mkdir', 'rmdir')),
    local_path VARCHAR(1000),
    remote_path VARCHAR(1000) NOT NULL,
    file_size BIGINT,
    transfer_speed_bps BIGINT,
    preserve_permissions BOOLEAN DEFAULT true,
    preserve_timestamps BOOLEAN DEFAULT true,
    recursive BOOLEAN DEFAULT false,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'failed')),
    error_message TEXT,
    files_transferred INTEGER DEFAULT 0,
    bytes_transferred BIGINT DEFAULT 0,
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for SFTP operations
CREATE INDEX IF NOT EXISTS idx_sftp_operations_job_run_step_id ON sftp_operations(job_run_step_id);
CREATE INDEX IF NOT EXISTS idx_sftp_operations_target_id ON sftp_operations(target_id);
CREATE INDEX IF NOT EXISTS idx_sftp_operations_operation_type ON sftp_operations(operation_type);
CREATE INDEX IF NOT EXISTS idx_sftp_operations_status ON sftp_operations(status);

-- Add Linux-specific target configuration
ALTER TABLE targets ADD COLUMN IF NOT EXISTS os_type VARCHAR(20) DEFAULT 'windows' CHECK (os_type IN ('windows', 'linux', 'unix', 'macos'));
ALTER TABLE targets ADD COLUMN IF NOT EXISTS ssh_port INTEGER DEFAULT 22;
ALTER TABLE targets ADD COLUMN IF NOT EXISTS ssh_host_key TEXT;
ALTER TABLE targets ADD COLUMN IF NOT EXISTS ssh_host_key_type VARCHAR(20) CHECK (ssh_host_key_type IN ('rsa', 'ed25519', 'ecdsa', 'dsa'));

-- Update existing targets to have os_type
UPDATE targets SET os_type = 'windows' WHERE os_type IS NULL;

-- Add SSH step types to job execution tracking
INSERT INTO step_types (name, description, category, schema) VALUES 
('ssh.exec', 'Execute command via SSH', 'ssh', '{
  "type": "object",
  "required": ["command", "target"],
  "properties": {
    "command": {"type": "string", "description": "Command to execute"},
    "target": {"type": "string", "description": "Target identifier"},
    "shell": {"type": "string", "enum": ["bash", "sh", "zsh", "fish", "csh", "tcsh"], "default": "bash"},
    "working_directory": {"type": "string", "description": "Working directory for command execution"},
    "environment": {"type": "object", "description": "Environment variables"},
    "timeout_sec": {"type": "integer", "minimum": 1, "default": 300}
  }
}'),
('sftp.upload', 'Upload file via SFTP', 'sftp', '{
  "type": "object",
  "required": ["local_path", "remote_path", "target"],
  "properties": {
    "local_path": {"type": "string", "description": "Local file or directory path"},
    "remote_path": {"type": "string", "description": "Remote destination path"},
    "target": {"type": "string", "description": "Target identifier"},
    "preserve_permissions": {"type": "boolean", "default": true},
    "preserve_timestamps": {"type": "boolean", "default": true},
    "recursive": {"type": "boolean", "default": false},
    "timeout_sec": {"type": "integer", "minimum": 1, "default": 300}
  }
}'),
('sftp.download', 'Download file via SFTP', 'sftp', '{
  "type": "object",
  "required": ["remote_path", "local_path", "target"],
  "properties": {
    "remote_path": {"type": "string", "description": "Remote file or directory path"},
    "local_path": {"type": "string", "description": "Local destination path"},
    "target": {"type": "string", "description": "Target identifier"},
    "preserve_permissions": {"type": "boolean", "default": true},
    "preserve_timestamps": {"type": "boolean", "default": true},
    "recursive": {"type": "boolean", "default": false},
    "timeout_sec": {"type": "integer", "minimum": 1, "default": 300}
  }
}'),
('sftp.sync', 'Synchronize directories via SFTP', 'sftp', '{
  "type": "object",
  "required": ["local_path", "remote_path", "target"],
  "properties": {
    "local_path": {"type": "string", "description": "Local directory path"},
    "remote_path": {"type": "string", "description": "Remote directory path"},
    "target": {"type": "string", "description": "Target identifier"},
    "direction": {"type": "string", "enum": ["upload", "download", "bidirectional"], "default": "upload"},
    "delete_extra": {"type": "boolean", "default": false, "description": "Delete files not present in source"},
    "preserve_permissions": {"type": "boolean", "default": true},
    "preserve_timestamps": {"type": "boolean", "default": true},
    "exclude_patterns": {"type": "array", "items": {"type": "string"}, "description": "File patterns to exclude"},
    "timeout_sec": {"type": "integer", "minimum": 1, "default": 600}
  }
}')
ON CONFLICT (name) DO UPDATE SET
  description = EXCLUDED.description,
  category = EXCLUDED.category,
  schema = EXCLUDED.schema;

-- Add comments for documentation
COMMENT ON TABLE ssh_connections IS 'Tracks SSH connection status and metadata for targets';
COMMENT ON TABLE ssh_executions IS 'Logs SSH command executions with results and timing';
COMMENT ON TABLE sftp_operations IS 'Tracks SFTP file operations with transfer statistics';
COMMENT ON COLUMN targets.os_type IS 'Operating system type for target-specific operations';
COMMENT ON COLUMN targets.ssh_port IS 'SSH port for Linux/Unix targets';
COMMENT ON COLUMN targets.ssh_host_key IS 'SSH host key for connection verification';

-- Update database statistics
ANALYZE ssh_connections;
ANALYZE ssh_executions;
ANALYZE sftp_operations;
ANALYZE targets;