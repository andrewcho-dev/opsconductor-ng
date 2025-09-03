-- Migration: Add os_type column to targets table
-- This adds OS type support for Linux/Unix targets

-- Add os_type column to targets table
ALTER TABLE targets ADD COLUMN IF NOT EXISTS os_type TEXT NOT NULL DEFAULT 'windows' 
CHECK (os_type IN ('windows', 'linux', 'unix', 'network', 'other'));

-- Create index for os_type
CREATE INDEX IF NOT EXISTS idx_targets_os_type ON targets(os_type);

-- Update credential types to include SSH key support
ALTER TABLE credentials DROP CONSTRAINT IF EXISTS credentials_credential_type_check;
ALTER TABLE credentials ADD CONSTRAINT credentials_credential_type_check 
CHECK (credential_type IN ('winrm', 'ssh', 'ssh_key', 'api_key', 'certificate', 'database', 'snmp'));

-- Update protocol types to include more options
ALTER TABLE targets DROP CONSTRAINT IF EXISTS targets_protocol_check;
ALTER TABLE targets ADD CONSTRAINT targets_protocol_check 
CHECK (protocol IN ('winrm', 'ssh', 'http', 'https', 'snmp', 'database'));

-- Set default os_type based on existing protocol
UPDATE targets SET os_type = 'windows' WHERE protocol = 'winrm' AND os_type = 'windows';
UPDATE targets SET os_type = 'linux' WHERE protocol = 'ssh' AND os_type = 'windows';