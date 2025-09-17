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
    -- Check if new targets table exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables 
                   WHERE table_schema = 'assets' AND table_name = 'targets') THEN
        RAISE EXCEPTION 'New assets.targets table not found! Please run complete-schema.sql first.';
    END IF;
    
    -- Check if tags table exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables 
                   WHERE table_schema = 'assets' AND table_name = 'tags') THEN
        RAISE EXCEPTION 'New assets.tags table not found! Please run complete-schema.sql first.';
    END IF;
    
    -- Check if target_tags table exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables 
                   WHERE table_schema = 'assets' AND table_name = 'target_tags') THEN
        RAISE EXCEPTION 'New assets.target_tags table not found! Please run complete-schema.sql first.';
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
        WHEN table_name = 'targets' THEN 'NEW - Core target table with all connection methods'
        WHEN table_name = 'tags' THEN 'NEW - Enhanced tag system'
        WHEN table_name = 'target_tags' THEN 'NEW - Target-tag relationships'
        ELSE 'OTHER - ' || table_name
    END as description
FROM information_schema.tables 
WHERE table_schema = 'assets' 
ORDER BY table_name;