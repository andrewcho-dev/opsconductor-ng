-- Credentials service database initialization
-- This script creates the credentials table as specified in the implementation plan

-- Create credentials table with AES-GCM encrypted blob storage
CREATE TABLE IF NOT EXISTS credentials (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  type TEXT NOT NULL CHECK (type IN ('winrm_ntlm', 'winrm_basic', 'winrm_kerberos', 'ssh_key')),
  enc_blob BYTEA NOT NULL,           -- AES-GCM: nonce(12)||ciphertext+tag (JSON inside)
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  rotated_at TIMESTAMPTZ
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_credentials_type ON credentials(type);
CREATE INDEX IF NOT EXISTS idx_credentials_created_at ON credentials(created_at);

-- Insert some sample data for testing (will be encrypted by the service)
-- Note: These are just placeholders - actual credentials will be encrypted by the service
INSERT INTO credentials (name, type, enc_blob, created_at) VALUES 
('sample-winrm-admin', 'winrm_ntlm', '\x000000000000000000000000000000000000000000000000', NOW())
ON CONFLICT (name) DO NOTHING;

-- Grant permissions (adjust based on your database setup)
-- GRANT ALL PRIVILEGES ON TABLE credentials TO your_service_user;
-- GRANT USAGE, SELECT ON SEQUENCE credentials_id_seq TO your_service_user;