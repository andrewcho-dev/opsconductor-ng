-- Keycloak Migration Preparation Script
-- This script prepares the database for Keycloak migration
-- It creates backup tables and migration tracking

-- Create migration tracking table
CREATE TABLE IF NOT EXISTS identity.migration_status (
    id SERIAL PRIMARY KEY,
    migration_name VARCHAR(100) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'pending', -- pending, in_progress, completed, failed
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create backup tables for current identity data
CREATE TABLE IF NOT EXISTS identity.users_backup AS 
SELECT * FROM identity.users WHERE 1=0;

CREATE TABLE IF NOT EXISTS identity.roles_backup AS 
SELECT * FROM identity.roles WHERE 1=0;

CREATE TABLE IF NOT EXISTS identity.user_roles_backup AS 
SELECT * FROM identity.user_roles WHERE 1=0;

CREATE TABLE IF NOT EXISTS identity.sessions_backup AS 
SELECT * FROM identity.user_sessions WHERE 1=0;

-- Create Keycloak user mapping table for migration tracking
CREATE TABLE IF NOT EXISTS identity.keycloak_user_mapping (
    id SERIAL PRIMARY KEY,
    legacy_user_id INTEGER REFERENCES identity.users(id),
    keycloak_user_id VARCHAR(36) NOT NULL, -- Keycloak UUID
    username VARCHAR(50) NOT NULL,
    email VARCHAR(255) NOT NULL,
    migrated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    migration_notes TEXT
);

-- Create Keycloak role mapping table
CREATE TABLE IF NOT EXISTS identity.keycloak_role_mapping (
    id SERIAL PRIMARY KEY,
    legacy_role_id INTEGER REFERENCES identity.roles(id),
    keycloak_role_name VARCHAR(50) NOT NULL,
    keycloak_role_id VARCHAR(36), -- Keycloak UUID
    migrated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    migration_notes TEXT
);

-- Insert initial migration status
INSERT INTO identity.migration_status (migration_name, status) 
VALUES ('keycloak_preparation', 'pending')
ON CONFLICT (migration_name) DO NOTHING;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_keycloak_user_mapping_legacy_id 
ON identity.keycloak_user_mapping(legacy_user_id);

CREATE INDEX IF NOT EXISTS idx_keycloak_user_mapping_keycloak_id 
ON identity.keycloak_user_mapping(keycloak_user_id);

CREATE INDEX IF NOT EXISTS idx_keycloak_role_mapping_legacy_id 
ON identity.keycloak_role_mapping(legacy_role_id);

-- Grant necessary permissions to keycloak schema
GRANT USAGE ON SCHEMA keycloak TO postgres;
GRANT CREATE ON SCHEMA keycloak TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA keycloak TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA keycloak TO postgres;

-- Update migration status
UPDATE identity.migration_status 
SET status = 'completed', completed_at = CURRENT_TIMESTAMP 
WHERE migration_name = 'keycloak_preparation';

-- Display current identity data summary
DO $$
DECLARE
    user_count INTEGER;
    role_count INTEGER;
    session_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO user_count FROM identity.users;
    SELECT COUNT(*) INTO role_count FROM identity.roles;
    SELECT COUNT(*) INTO session_count FROM identity.user_sessions;
    
    RAISE NOTICE 'Keycloak Migration Preparation Complete:';
    RAISE NOTICE '  - Users to migrate: %', user_count;
    RAISE NOTICE '  - Roles to migrate: %', role_count;
    RAISE NOTICE '  - Active sessions: %', session_count;
    RAISE NOTICE '  - Backup tables created';
    RAISE NOTICE '  - Migration tracking tables created';
    RAISE NOTICE '  - Keycloak schema permissions granted';
END $$;