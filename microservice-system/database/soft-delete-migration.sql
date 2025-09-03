-- Soft Delete Migration
-- Add deleted_at columns to all tables that need soft delete functionality

-- Add soft delete to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ DEFAULT NULL;
CREATE INDEX IF NOT EXISTS idx_users_deleted_at ON users(deleted_at);

-- Add soft delete to credentials table
ALTER TABLE credentials ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ DEFAULT NULL;
CREATE INDEX IF NOT EXISTS idx_credentials_deleted_at ON credentials(deleted_at);

-- Add soft delete to targets table
ALTER TABLE targets ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ DEFAULT NULL;
CREATE INDEX IF NOT EXISTS idx_targets_deleted_at ON targets(deleted_at);

-- Add soft delete to jobs table
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ DEFAULT NULL;
CREATE INDEX IF NOT EXISTS idx_jobs_deleted_at ON jobs(deleted_at);

-- Add soft delete to job_runs table
ALTER TABLE job_runs ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ DEFAULT NULL;
CREATE INDEX IF NOT EXISTS idx_job_runs_deleted_at ON job_runs(deleted_at);

-- Add soft delete to job_run_steps table
ALTER TABLE job_run_steps ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ DEFAULT NULL;
CREATE INDEX IF NOT EXISTS idx_job_run_steps_deleted_at ON job_run_steps(deleted_at);

-- Add soft delete to schedules table (if exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'schedules') THEN
        ALTER TABLE schedules ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ DEFAULT NULL;
        CREATE INDEX IF NOT EXISTS idx_schedules_deleted_at ON schedules(deleted_at);
    END IF;
END $$;

-- Add soft delete to notification_templates table (if exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'notification_templates') THEN
        ALTER TABLE notification_templates ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ DEFAULT NULL;
        CREATE INDEX IF NOT EXISTS idx_notification_templates_deleted_at ON notification_templates(deleted_at);
    END IF;
END $$;

-- Update unique constraints to exclude soft-deleted records
-- Drop existing unique constraint on targets.name
ALTER TABLE targets DROP CONSTRAINT IF EXISTS targets_name_key;

-- Create partial unique index that excludes soft-deleted records
CREATE UNIQUE INDEX IF NOT EXISTS idx_targets_name_unique_not_deleted 
ON targets(name) WHERE deleted_at IS NULL;

-- Drop existing unique constraint on credentials.name
ALTER TABLE credentials DROP CONSTRAINT IF EXISTS credentials_name_key;

-- Create partial unique index that excludes soft-deleted records
CREATE UNIQUE INDEX IF NOT EXISTS idx_credentials_name_unique_not_deleted 
ON credentials(name) WHERE deleted_at IS NULL;

-- Drop existing unique constraint on users.email
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_email_key;

-- Create partial unique index that excludes soft-deleted records
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_unique_not_deleted 
ON users(email) WHERE deleted_at IS NULL;

-- Drop existing unique constraint on users.username
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_username_key;

-- Create partial unique index that excludes soft-deleted records
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username_unique_not_deleted 
ON users(username) WHERE deleted_at IS NULL;