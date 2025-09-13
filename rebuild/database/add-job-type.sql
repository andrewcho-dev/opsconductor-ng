-- Migration: Add job_type column to automation.jobs table
-- This allows categorizing jobs (compliance, remediation, etc.)
-- for proper result routing while keeping execution logic unified

BEGIN;

-- Add job_type column
ALTER TABLE automation.jobs 
ADD COLUMN job_type VARCHAR(50) NOT NULL DEFAULT 'general';

-- Add index for efficient filtering by job type
CREATE INDEX idx_jobs_job_type ON automation.jobs(job_type);



-- Add comment for documentation
COMMENT ON COLUMN automation.jobs.job_type IS 'Job category for result routing (compliance, remediation, etc.)';

COMMIT;