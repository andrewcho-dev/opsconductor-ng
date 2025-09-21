-- Cleanup Script: Remove Old Target Tables
-- This script removes the old multi-table target system

-- ============================================================================
-- REMOVE OLD TARGET TABLES
-- ============================================================================

-- Drop old tables in correct order (respecting foreign key constraints)
DROP TABLE IF EXISTS assets.target_group_memberships CASCADE;
DROP TABLE IF EXISTS assets.target_services CASCADE;
DROP TABLE IF EXISTS assets.enhanced_targets CASCADE;
DROP TABLE IF EXISTS assets.target_groups CASCADE;
DROP TABLE IF EXISTS assets.service_definitions CASCADE;
DROP TABLE IF EXISTS assets.target_credentials CASCADE;

-- Drop old indexes that might still exist
DROP INDEX IF EXISTS idx_target_services_one_default;
DROP INDEX IF EXISTS idx_enhanced_targets_hostname;
DROP INDEX IF EXISTS idx_enhanced_targets_ip;
DROP INDEX IF EXISTS idx_target_services_target_id;
DROP INDEX IF EXISTS idx_target_group_memberships_target_id;
DROP INDEX IF EXISTS idx_target_group_memberships_group_id;

-- Drop old functions that might reference old tables
DROP FUNCTION IF EXISTS assets.get_target_services(INTEGER);
DROP FUNCTION IF EXISTS assets.validate_target_group_hierarchy();

-- ============================================================================
-- VERIFY NEW SCHEMA IS IN PLACE
-- ============================================================================

-- Verify new tables exist
DO $$
BEGIN
    -- Check if new assets table exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables 
                   WHERE table_schema = 'assets' AND table_name = 'assets') THEN
        RAISE EXCEPTION 'New assets.assets table not found! Please run consolidate-assets-schema.sql first.';
    END IF;
    
    RAISE NOTICE 'New schema verification passed. Old tables cleaned up successfully.';
END $$;

-- ============================================================================
-- SUMMARY
-- ============================================================================

-- Show remaining tables in assets schema
SELECT 
    table_name,
    CASE 
        WHEN table_name = 'assets' THEN 'NEW - Consolidated assets table with all target information'
        WHEN table_name LIKE 'backup_%' THEN 'BACKUP - Backup of old schema tables'
        ELSE 'OTHER - ' || table_name
    END as description
FROM information_schema.tables 
WHERE table_schema = 'assets' 
ORDER BY table_name;