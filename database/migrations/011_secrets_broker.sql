-- Migration 011: Secrets Broker for Asset Credentials
-- Provides secure server-side credential storage for host connections

CREATE SCHEMA IF NOT EXISTS secrets;

-- Secrets table for storing encrypted credentials
CREATE TABLE IF NOT EXISTS secrets.host_credentials (
    id SERIAL PRIMARY KEY,
    host VARCHAR(255) NOT NULL, -- hostname or IP
    purpose VARCHAR(50) NOT NULL, -- 'winrm', 'ssh', 'rdp', 'http', etc.
    username VARCHAR(255),
    password_encrypted TEXT, -- AES-256-GCM encrypted
    domain VARCHAR(255), -- For Windows domain authentication
    additional_data JSONB DEFAULT '{}', -- For extra fields like private keys, tokens
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_by VARCHAR(100),
    
    -- Ensure one credential per host+purpose combination
    UNIQUE(host, purpose)
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_host_credentials_host ON secrets.host_credentials(host);
CREATE INDEX IF NOT EXISTS idx_host_credentials_purpose ON secrets.host_credentials(purpose);
CREATE INDEX IF NOT EXISTS idx_host_credentials_host_purpose ON secrets.host_credentials(host, purpose);

-- Audit log for credential access
CREATE TABLE IF NOT EXISTS secrets.credential_access_log (
    id SERIAL PRIMARY KEY,
    credential_id INTEGER REFERENCES secrets.host_credentials(id) ON DELETE CASCADE,
    host VARCHAR(255) NOT NULL,
    purpose VARCHAR(50) NOT NULL,
    accessed_by VARCHAR(100), -- Service or user that accessed
    access_type VARCHAR(50) NOT NULL, -- 'read', 'create', 'update', 'delete'
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    ip_address INET,
    accessed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_credential_access_log_credential_id ON secrets.credential_access_log(credential_id);
CREATE INDEX IF NOT EXISTS idx_credential_access_log_accessed_at ON secrets.credential_access_log(accessed_at);
CREATE INDEX IF NOT EXISTS idx_credential_access_log_host ON secrets.credential_access_log(host);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION secrets.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update updated_at
CREATE TRIGGER update_host_credentials_updated_at BEFORE UPDATE
    ON secrets.host_credentials FOR EACH ROW
    EXECUTE FUNCTION secrets.update_updated_at_column();

COMMENT ON TABLE secrets.host_credentials IS 'Encrypted credentials for host connections (WinRM, SSH, etc.)';
COMMENT ON TABLE secrets.credential_access_log IS 'Audit log for all credential access operations';