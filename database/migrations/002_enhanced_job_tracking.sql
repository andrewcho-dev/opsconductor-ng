-- Migration: Enhanced Job Tracking and Monitoring Schema
-- Date: 2024-01-XX
-- Description: Add comprehensive job tracking, scheduling, and monitoring capabilities

-- Add Celery task tracking to job_runs
ALTER TABLE job_runs 
ADD COLUMN IF NOT EXISTS celery_task_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS worker_hostname VARCHAR(255),
ADD COLUMN IF NOT EXISTS queue_name VARCHAR(100) DEFAULT 'celery',
ADD COLUMN IF NOT EXISTS execution_time_ms INTEGER,
ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0;

-- Add indexes for Celery task tracking
CREATE INDEX IF NOT EXISTS idx_job_runs_celery_task_id ON job_runs(celery_task_id);
CREATE INDEX IF NOT EXISTS idx_job_runs_worker_hostname ON job_runs(worker_hostname);
CREATE INDEX IF NOT EXISTS idx_job_runs_queue_name ON job_runs(queue_name);

-- Job scheduling table for recurring and scheduled jobs
CREATE TABLE IF NOT EXISTS job_schedules (
    id BIGSERIAL PRIMARY KEY,
    job_id BIGINT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    schedule_type VARCHAR(50) NOT NULL CHECK (schedule_type IN ('once', 'recurring', 'cron')),
    cron_expression VARCHAR(100), -- For cron-based schedules
    interval_seconds INTEGER, -- For interval-based schedules
    next_run_at TIMESTAMPTZ,
    last_run_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT true,
    max_runs INTEGER, -- NULL for unlimited
    run_count INTEGER DEFAULT 0,
    parameters JSONB DEFAULT '{}',
    created_by BIGINT NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for job_schedules
CREATE INDEX IF NOT EXISTS idx_job_schedules_job_id ON job_schedules(job_id);
CREATE INDEX IF NOT EXISTS idx_job_schedules_next_run_at ON job_schedules(next_run_at);
CREATE INDEX IF NOT EXISTS idx_job_schedules_is_active ON job_schedules(is_active);
CREATE INDEX IF NOT EXISTS idx_job_schedules_schedule_type ON job_schedules(schedule_type);
CREATE INDEX IF NOT EXISTS idx_job_schedules_created_by ON job_schedules(created_by);

-- Job execution metrics and monitoring
CREATE TABLE IF NOT EXISTS job_execution_metrics (
    id BIGSERIAL PRIMARY KEY,
    job_run_id BIGINT NOT NULL REFERENCES job_runs(id) ON DELETE CASCADE,
    step_id BIGINT REFERENCES job_run_steps(id) ON DELETE CASCADE,
    metric_type VARCHAR(50) NOT NULL, -- 'execution_time', 'memory_usage', 'cpu_usage', etc.
    metric_value DECIMAL(15,6) NOT NULL,
    metric_unit VARCHAR(20) NOT NULL, -- 'ms', 'mb', 'percent', etc.
    recorded_at TIMESTAMPTZ DEFAULT NOW(),
    worker_hostname VARCHAR(255),
    additional_data JSONB
);

-- Indexes for job_execution_metrics
CREATE INDEX IF NOT EXISTS idx_job_execution_metrics_job_run_id ON job_execution_metrics(job_run_id);
CREATE INDEX IF NOT EXISTS idx_job_execution_metrics_step_id ON job_execution_metrics(step_id);
CREATE INDEX IF NOT EXISTS idx_job_execution_metrics_type ON job_execution_metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_job_execution_metrics_recorded_at ON job_execution_metrics(recorded_at);

-- Large output and artifact storage references
CREATE TABLE IF NOT EXISTS job_artifacts (
    id BIGSERIAL PRIMARY KEY,
    job_run_id BIGINT NOT NULL REFERENCES job_runs(id) ON DELETE CASCADE,
    step_id BIGINT REFERENCES job_run_steps(id) ON DELETE CASCADE,
    artifact_type VARCHAR(50) NOT NULL, -- 'stdout', 'stderr', 'file', 'log', 'screenshot'
    artifact_name VARCHAR(255) NOT NULL,
    storage_type VARCHAR(50) NOT NULL, -- 'database', 's3', 'filesystem', 'minio'
    storage_path TEXT,
    file_size_bytes BIGINT,
    content_type VARCHAR(100),
    checksum_sha256 VARCHAR(64),
    compression_type VARCHAR(20), -- 'none', 'gzip', 'bzip2'
    retention_days INTEGER DEFAULT 30,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ
);

-- Indexes for job_artifacts
CREATE INDEX IF NOT EXISTS idx_job_artifacts_job_run_id ON job_artifacts(job_run_id);
CREATE INDEX IF NOT EXISTS idx_job_artifacts_step_id ON job_artifacts(step_id);
CREATE INDEX IF NOT EXISTS idx_job_artifacts_type ON job_artifacts(artifact_type);
CREATE INDEX IF NOT EXISTS idx_job_artifacts_storage_type ON job_artifacts(storage_type);
CREATE INDEX IF NOT EXISTS idx_job_artifacts_expires_at ON job_artifacts(expires_at);

-- Celery worker health and status tracking
CREATE TABLE IF NOT EXISTS celery_workers (
    id BIGSERIAL PRIMARY KEY,
    hostname VARCHAR(255) NOT NULL UNIQUE,
    worker_name VARCHAR(255) NOT NULL,
    queues TEXT[], -- Array of queue names this worker processes
    status VARCHAR(50) NOT NULL DEFAULT 'unknown', -- 'online', 'offline', 'busy', 'idle'
    last_heartbeat TIMESTAMPTZ DEFAULT NOW(),
    active_tasks INTEGER DEFAULT 0,
    processed_tasks BIGINT DEFAULT 0,
    failed_tasks BIGINT DEFAULT 0,
    load_average DECIMAL(5,2),
    memory_usage_mb INTEGER,
    cpu_usage_percent DECIMAL(5,2),
    version VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for celery_workers
CREATE INDEX IF NOT EXISTS idx_celery_workers_hostname ON celery_workers(hostname);
CREATE INDEX IF NOT EXISTS idx_celery_workers_status ON celery_workers(status);
CREATE INDEX IF NOT EXISTS idx_celery_workers_last_heartbeat ON celery_workers(last_heartbeat);

-- Queue monitoring and statistics
CREATE TABLE IF NOT EXISTS queue_statistics (
    id BIGSERIAL PRIMARY KEY,
    queue_name VARCHAR(100) NOT NULL,
    pending_tasks INTEGER DEFAULT 0,
    active_tasks INTEGER DEFAULT 0,
    completed_tasks BIGINT DEFAULT 0,
    failed_tasks BIGINT DEFAULT 0,
    avg_processing_time_ms INTEGER,
    max_processing_time_ms INTEGER,
    min_processing_time_ms INTEGER,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for queue_statistics
CREATE INDEX IF NOT EXISTS idx_queue_statistics_queue_name ON queue_statistics(queue_name);
CREATE INDEX IF NOT EXISTS idx_queue_statistics_recorded_at ON queue_statistics(recorded_at);

-- Job run dependencies for complex workflows
CREATE TABLE IF NOT EXISTS job_run_dependencies (
    id BIGSERIAL PRIMARY KEY,
    job_run_id BIGINT NOT NULL REFERENCES job_runs(id) ON DELETE CASCADE,
    depends_on_job_run_id BIGINT NOT NULL REFERENCES job_runs(id) ON DELETE CASCADE,
    dependency_type VARCHAR(50) NOT NULL DEFAULT 'success', -- 'success', 'completion', 'failure'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(job_run_id, depends_on_job_run_id)
);

-- Indexes for job_run_dependencies
CREATE INDEX IF NOT EXISTS idx_job_run_dependencies_job_run_id ON job_run_dependencies(job_run_id);
CREATE INDEX IF NOT EXISTS idx_job_run_dependencies_depends_on ON job_run_dependencies(depends_on_job_run_id);

-- Add missing columns to job_run_steps for better tracking
ALTER TABLE job_run_steps 
ADD COLUMN IF NOT EXISTS celery_task_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS worker_hostname VARCHAR(255),
ADD COLUMN IF NOT EXISTS execution_time_ms INTEGER,
ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS max_retries INTEGER DEFAULT 3;

-- Indexes for enhanced job_run_steps
CREATE INDEX IF NOT EXISTS idx_job_run_steps_celery_task_id ON job_run_steps(celery_task_id);
CREATE INDEX IF NOT EXISTS idx_job_run_steps_worker_hostname ON job_run_steps(worker_hostname);

-- Views for monitoring and reporting
CREATE OR REPLACE VIEW job_run_summary AS
SELECT 
    jr.id,
    jr.job_id,
    j.name as job_name,
    jr.status,
    jr.requested_by,
    u.username as requested_by_username,
    jr.queued_at,
    jr.started_at,
    jr.finished_at,
    jr.execution_time_ms,
    jr.worker_hostname,
    jr.queue_name,
    jr.retry_count,
    jr.correlation_id,
    (SELECT COUNT(*) FROM job_run_steps jrs WHERE jrs.job_run_id = jr.id) as total_steps,
    (SELECT COUNT(*) FROM job_run_steps jrs WHERE jrs.job_run_id = jr.id AND jrs.status = 'succeeded') as succeeded_steps,
    (SELECT COUNT(*) FROM job_run_steps jrs WHERE jrs.job_run_id = jr.id AND jrs.status = 'failed') as failed_steps,
    (SELECT COUNT(*) FROM job_run_steps jrs WHERE jrs.job_run_id = jr.id AND jrs.status = 'running') as running_steps
FROM job_runs jr
JOIN jobs j ON jr.job_id = j.id
LEFT JOIN users u ON jr.requested_by = u.id;

-- View for queue monitoring
CREATE OR REPLACE VIEW queue_health_summary AS
SELECT 
    queue_name,
    COUNT(*) as total_jobs,
    COUNT(*) FILTER (WHERE status = 'queued') as queued_jobs,
    COUNT(*) FILTER (WHERE status = 'running') as running_jobs,
    COUNT(*) FILTER (WHERE status = 'succeeded') as succeeded_jobs,
    COUNT(*) FILTER (WHERE status = 'failed') as failed_jobs,
    AVG(execution_time_ms) as avg_execution_time_ms,
    MAX(execution_time_ms) as max_execution_time_ms,
    MIN(execution_time_ms) as min_execution_time_ms
FROM job_runs 
WHERE queue_name IS NOT NULL
GROUP BY queue_name;

-- Function to cleanup old job artifacts
CREATE OR REPLACE FUNCTION cleanup_expired_artifacts()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM job_artifacts 
    WHERE expires_at IS NOT NULL AND expires_at < NOW();
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to update job schedule next run time
CREATE OR REPLACE FUNCTION update_schedule_next_run(schedule_id BIGINT)
RETURNS VOID AS $$
DECLARE
    schedule_rec RECORD;
    next_run TIMESTAMPTZ;
BEGIN
    SELECT * INTO schedule_rec FROM job_schedules WHERE id = schedule_id;
    
    IF schedule_rec.schedule_type = 'once' THEN
        -- One-time schedule, deactivate after execution
        UPDATE job_schedules SET is_active = false WHERE id = schedule_id;
    ELSIF schedule_rec.schedule_type = 'recurring' AND schedule_rec.interval_seconds IS NOT NULL THEN
        -- Interval-based recurring schedule
        next_run := NOW() + INTERVAL '1 second' * schedule_rec.interval_seconds;
        UPDATE job_schedules SET next_run_at = next_run, run_count = run_count + 1 WHERE id = schedule_id;
    ELSIF schedule_rec.schedule_type = 'cron' AND schedule_rec.cron_expression IS NOT NULL THEN
        -- Cron-based schedule (requires external cron parser)
        -- This would need to be implemented with a cron parsing function
        -- For now, just increment run_count
        UPDATE job_schedules SET run_count = run_count + 1 WHERE id = schedule_id;
    END IF;
    
    -- Check max_runs limit
    IF schedule_rec.max_runs IS NOT NULL AND schedule_rec.run_count >= schedule_rec.max_runs THEN
        UPDATE job_schedules SET is_active = false WHERE id = schedule_id;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Comments for documentation
COMMENT ON TABLE job_schedules IS 'Stores job scheduling information for recurring and one-time scheduled jobs';
COMMENT ON TABLE job_execution_metrics IS 'Stores detailed execution metrics for jobs and steps';
COMMENT ON TABLE job_artifacts IS 'References to large outputs and artifacts stored outside the database';
COMMENT ON TABLE celery_workers IS 'Tracks Celery worker health and status';
COMMENT ON TABLE queue_statistics IS 'Stores queue performance statistics over time';
COMMENT ON TABLE job_run_dependencies IS 'Defines dependencies between job runs for complex workflows';

COMMENT ON COLUMN job_runs.celery_task_id IS 'Celery task ID for tracking execution';
COMMENT ON COLUMN job_runs.worker_hostname IS 'Hostname of the worker that executed the job';
COMMENT ON COLUMN job_runs.queue_name IS 'Name of the Celery queue used for execution';
COMMENT ON COLUMN job_runs.execution_time_ms IS 'Total execution time in milliseconds';