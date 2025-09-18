-- OpsConductor - Consolidate Assets Schema Migration
-- This script consolidates all target/asset information into a single table
-- and purges the old multi-table structure

-- ============================================================================
-- CREATE NEW CONSOLIDATED ASSETS TABLE
-- ============================================================================

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
-- MIGRATE DATA FROM OLD TABLES TO NEW CONSOLIDATED TABLE
-- ============================================================================

-- Migrate from enhanced_targets with their primary service
INSERT INTO assets.assets (
    name, hostname, ip_address, description, tags, os_type, os_version,
    service_type, port, is_secure, credential_type, username, password_encrypted,
    private_key_encrypted, public_key, api_key_encrypted, bearer_token_encrypted,
    certificate_encrypted, passphrase_encrypted, domain, additional_services,
    is_active, connection_status, last_tested_at, notes, created_by, created_at, updated_at
)
SELECT 
    et.name,
    et.hostname,
    et.ip_address,
    et.description,
    et.tags,
    et.os_type,
    et.os_version,
    -- Primary service (default service or first service)
    COALESCE(primary_svc.service_type, 'ssh') as service_type,
    COALESCE(primary_svc.port, 22) as port,
    COALESCE(primary_svc.is_secure, false) as is_secure,
    primary_svc.credential_type,
    primary_svc.username,
    primary_svc.password_encrypted,
    primary_svc.private_key_encrypted,
    primary_svc.public_key,
    primary_svc.api_key_encrypted,
    primary_svc.bearer_token_encrypted,
    primary_svc.certificate_encrypted,
    primary_svc.passphrase_encrypted,
    primary_svc.domain,
    -- Additional services (all non-primary services as JSON array)
    COALESCE(
        (SELECT jsonb_agg(
            jsonb_build_object(
                'service_type', ts.service_type,
                'port', ts.port,
                'is_secure', ts.is_secure,
                'credential_type', ts.credential_type,
                'username', ts.username,
                'password_encrypted', ts.password_encrypted,
                'private_key_encrypted', ts.private_key_encrypted,
                'public_key', ts.public_key,
                'api_key_encrypted', ts.api_key_encrypted,
                'bearer_token_encrypted', ts.bearer_token_encrypted,
                'certificate_encrypted', ts.certificate_encrypted,
                'passphrase_encrypted', ts.passphrase_encrypted,
                'domain', ts.domain,
                'notes', ts.notes
            )
        )
        FROM assets.target_services ts 
        WHERE ts.target_id = et.id 
        AND ts.is_default = false
        AND ts.is_enabled = true),
        '[]'::jsonb
    ) as additional_services,
    true as is_active,
    primary_svc.connection_status,
    primary_svc.last_tested_at,
    primary_svc.notes,
    1 as created_by, -- Default to admin user
    et.created_at,
    et.updated_at
FROM assets.enhanced_targets et
LEFT JOIN (
    -- Get the primary (default) service for each target
    SELECT DISTINCT ON (target_id) *
    FROM assets.target_services
    WHERE is_enabled = true
    ORDER BY target_id, is_default DESC, id ASC
) primary_svc ON primary_svc.target_id = et.id
WHERE EXISTS (SELECT 1 FROM assets.enhanced_targets WHERE id = et.id);

-- Migrate from legacy targets table (if no enhanced_targets exist)
INSERT INTO assets.assets (
    name, hostname, ip_address, description, tags, os_type, os_version,
    service_type, port, is_secure, credential_type, username, password_encrypted,
    additional_services, is_active, created_by, created_at, updated_at
)
SELECT 
    t.name,
    t.host as hostname,
    t.host as ip_address, -- Use host as IP for legacy
    t.description,
    t.tags,
    CASE 
        WHEN t.target_type = 'windows' THEN 'windows'
        WHEN t.target_type = 'linux' THEN 'linux'
        ELSE 'other'
    END as os_type,
    NULL as os_version,
    -- Map connection_type to service_type
    CASE 
        WHEN t.connection_type = 'ssh' THEN 'ssh'
        WHEN t.connection_type = 'winrm' THEN 'winrm'
        WHEN t.connection_type = 'http' THEN 'http'
        WHEN t.connection_type = 'https' THEN 'https'
        WHEN t.connection_type = 'snmp' THEN 'snmp'
        ELSE 'ssh'
    END as service_type,
    COALESCE(t.port, 
        CASE 
            WHEN t.connection_type = 'ssh' THEN 22
            WHEN t.connection_type = 'winrm' THEN 5985
            WHEN t.connection_type = 'http' THEN 80
            WHEN t.connection_type = 'https' THEN 443
            WHEN t.connection_type = 'snmp' THEN 161
            ELSE 22
        END
    ) as port,
    CASE WHEN t.connection_type IN ('https', 'winrm_https') THEN true ELSE false END as is_secure,
    'username_password' as credential_type, -- Default for legacy
    NULL as username, -- Will be populated from credentials if available
    tc.encrypted_credentials as password_encrypted, -- Legacy encrypted credentials
    '[]'::jsonb as additional_services,
    t.is_active,
    t.created_by,
    t.created_at,
    t.updated_at
FROM assets.targets t
LEFT JOIN assets.target_credentials tc ON tc.target_id = t.id
WHERE NOT EXISTS (SELECT 1 FROM assets.enhanced_targets WHERE hostname = t.host)
AND EXISTS (SELECT 1 FROM assets.targets WHERE id = t.id);

-- ============================================================================
-- CREATE INDEXES FOR PERFORMANCE
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_assets_hostname ON assets.assets(hostname);
CREATE INDEX IF NOT EXISTS idx_assets_ip_address ON assets.assets(ip_address);
CREATE INDEX IF NOT EXISTS idx_assets_os_type ON assets.assets(os_type);
CREATE INDEX IF NOT EXISTS idx_assets_service_type ON assets.assets(service_type);
CREATE INDEX IF NOT EXISTS idx_assets_is_active ON assets.assets(is_active);
CREATE INDEX IF NOT EXISTS idx_assets_created_at ON assets.assets(created_at);
CREATE INDEX IF NOT EXISTS idx_assets_tags ON assets.assets USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_assets_additional_services ON assets.assets USING GIN(additional_services);

-- ============================================================================
-- PURGE OLD TABLES (BACKUP FIRST!)
-- ============================================================================

-- Create backup tables before dropping (just in case)
CREATE TABLE IF NOT EXISTS assets.backup_enhanced_targets AS SELECT * FROM assets.enhanced_targets;
CREATE TABLE IF NOT EXISTS assets.backup_target_services AS SELECT * FROM assets.target_services;
CREATE TABLE IF NOT EXISTS assets.backup_targets AS SELECT * FROM assets.targets;
CREATE TABLE IF NOT EXISTS assets.backup_target_credentials AS SELECT * FROM assets.target_credentials;
CREATE TABLE IF NOT EXISTS assets.backup_target_groups AS SELECT * FROM assets.target_groups;
CREATE TABLE IF NOT EXISTS assets.backup_target_group_memberships AS SELECT * FROM assets.target_group_memberships;
CREATE TABLE IF NOT EXISTS assets.backup_service_definitions AS SELECT * FROM assets.service_definitions;

-- Drop old indexes first
DROP INDEX IF EXISTS idx_target_services_one_default;
DROP INDEX IF EXISTS idx_enhanced_targets_ip;
DROP INDEX IF EXISTS idx_enhanced_targets_hostname;
DROP INDEX IF EXISTS idx_enhanced_targets_os_type;
DROP INDEX IF EXISTS idx_target_services_target_id;
DROP INDEX IF EXISTS idx_target_services_service_type;
DROP INDEX IF EXISTS idx_targets_host;
DROP INDEX IF EXISTS idx_targets_type;
DROP INDEX IF EXISTS idx_targets_active;

-- Drop old tables
DROP TABLE IF EXISTS assets.target_group_memberships CASCADE;
DROP TABLE IF EXISTS assets.target_groups CASCADE;
DROP TABLE IF EXISTS assets.target_services CASCADE;
DROP TABLE IF EXISTS assets.target_credentials CASCADE;
DROP TABLE IF EXISTS assets.enhanced_targets CASCADE;
DROP TABLE IF EXISTS assets.targets CASCADE;
DROP TABLE IF EXISTS assets.service_definitions CASCADE;

-- ============================================================================
-- UPDATE COMPLETE SCHEMA TO REFLECT CHANGES
-- ============================================================================

COMMENT ON TABLE assets.assets IS 'Consolidated assets table containing all target/asset information including services and credentials';
COMMENT ON COLUMN assets.assets.additional_services IS 'JSON array of additional services, each with their own credentials';
COMMENT ON COLUMN assets.assets.credential_type IS 'Type of credential for primary service: username_password, ssh_key, api_key, bearer_token, certificate';

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Assets schema consolidation completed successfully!';
    RAISE NOTICE 'Old tables have been backed up with "backup_" prefix';
    RAISE NOTICE 'New consolidated assets.assets table is ready for use';
END $$;