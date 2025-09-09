-- Migration: Add Phase 2 columns to job_runs table
-- Date: 2024-01-XX
-- Description: Add result_data and error_message columns for RabbitMQ-based job execution

-- Add result_data column to store execution results
ALTER TABLE job_runs 
ADD COLUMN IF NOT EXISTS result_data JSONB DEFAULT NULL;

-- Add error_message column to store error details
ALTER TABLE job_runs 
ADD COLUMN IF NOT EXISTS error_message TEXT DEFAULT NULL;

-- Add index for result_data JSONB column
CREATE INDEX IF NOT EXISTS idx_job_runs_result_data_gin ON job_runs USING GIN(result_data);

-- Add index for error_message for failed job queries
CREATE INDEX IF NOT EXISTS idx_job_runs_error_message ON job_runs(error_message) WHERE error_message IS NOT NULL;

-- Update the status check constraint to ensure consistency
-- (This will recreate the constraint with the same values)
ALTER TABLE job_runs DROP CONSTRAINT IF EXISTS job_runs_status_check;
ALTER TABLE job_runs ADD CONSTRAINT job_runs_status_check 
    CHECK (status IN ('queued','running','succeeded','failed','canceled'));

-- Add comment to document the new columns
COMMENT ON COLUMN job_runs.result_data IS 'JSON data containing job execution results and metrics';
COMMENT ON COLUMN job_runs.error_message IS 'Error message for failed job executions';