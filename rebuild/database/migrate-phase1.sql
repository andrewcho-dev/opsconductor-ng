-- Phase 1 Migration: Add missing columns to users table
-- This migration adds telephone and title columns if they don't exist

-- Check if columns exist and add them if missing
DO $$
BEGIN
    -- Add telephone column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'identity' 
        AND table_name = 'users' 
        AND column_name = 'telephone'
    ) THEN
        ALTER TABLE identity.users ADD COLUMN telephone VARCHAR(20);
    END IF;
    
    -- Add title column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'identity' 
        AND table_name = 'users' 
        AND column_name = 'title'
    ) THEN
        ALTER TABLE identity.users ADD COLUMN title VARCHAR(100);
    END IF;
END $$;

-- Update the admin user to have proper role assignment if not already assigned
INSERT INTO identity.user_roles (user_id, role_id, assigned_by)
SELECT 1, 1, 1
WHERE NOT EXISTS (
    SELECT 1 FROM identity.user_roles WHERE user_id = 1 AND role_id = 1
);

COMMIT;