-- Targets service database initialization
-- This script creates the targets table as specified in the implementation plan

-- Create targets table with WinRM and SSH configuration support
CREATE TABLE IF NOT EXISTS targets (
  id BIGSERIAL PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  protocol TEXT NOT NULL DEFAULT 'winrm' CHECK (protocol IN ('winrm', 'ssh')),
  hostname TEXT NOT NULL,
  port INT NOT NULL DEFAULT 5986,
  winrm_use_https BOOLEAN NOT NULL DEFAULT true,
  winrm_validate_cert BOOLEAN NOT NULL DEFAULT true,
  domain TEXT,
  credential_ref BIGINT NOT NULL, -- References credentials(id) but no FK constraint for cross-service reference
  tags JSONB NOT NULL DEFAULT '{}'::jsonb,
  depends_on BIGINT[], -- Array of target IDs for dependency tracking
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_targets_protocol ON targets(protocol);
CREATE INDEX IF NOT EXISTS idx_targets_tags_gin ON targets USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_targets_hostname ON targets(hostname);
CREATE INDEX IF NOT EXISTS idx_targets_created_at ON targets(created_at);
CREATE INDEX IF NOT EXISTS idx_targets_credential_ref ON targets(credential_ref);

-- Insert some sample data for testing
INSERT INTO targets (name, protocol, hostname, port, winrm_use_https, winrm_validate_cert, domain, credential_ref, tags, depends_on, created_at) VALUES 
('sample-windows-server', 'winrm', 'win-server-01.example.com', 5986, true, true, 'EXAMPLE', 1, '{"environment": "dev", "role": "web-server"}', '{}', NOW()),
('sample-linux-server', 'ssh', 'linux-server-01.example.com', 22, false, false, null, 2, '{"environment": "dev", "role": "database"}', '{}', NOW())
ON CONFLICT (name) DO NOTHING;

-- Grant permissions (adjust based on your database setup)
-- GRANT ALL PRIVILEGES ON TABLE targets TO your_service_user;
-- GRANT USAGE, SELECT ON SEQUENCE targets_id_seq TO your_service_user;