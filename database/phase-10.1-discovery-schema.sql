-- Phase 10.1: Discovery Service Database Schema
-- Discovery operations tracking
CREATE TABLE IF NOT EXISTS discovery_jobs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    discovery_type VARCHAR(50) NOT NULL, -- 'network_scan', 'ad_query', 'cloud_api'
    config JSONB NOT NULL,              -- Discovery configuration
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed', 'cancelled'
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    results_summary JSONB                -- Summary of discovered targets
);

-- Discovered targets (before import to main targets table)
CREATE TABLE IF NOT EXISTS discovered_targets (
    id SERIAL PRIMARY KEY,
    discovery_job_id INTEGER REFERENCES discovery_jobs(id),
    hostname VARCHAR(255),
    ip_address INET NOT NULL,
    os_type VARCHAR(50),                 -- Detected OS
    os_version VARCHAR(255),
    services JSONB,                      -- Detected services (WinRM, SSH, etc.)
    preferred_service JSONB,             -- Auto-selected preferred service (HTTPS over HTTP)
    connection_test_results JSONB,       -- Test results for each service
    system_info JSONB,                   -- Additional system information
    duplicate_status VARCHAR(50) DEFAULT 'none', -- 'none', 'potential_duplicate', 'confirmed_duplicate'
    existing_target_id INTEGER REFERENCES targets(id), -- Reference to existing target if duplicate
    import_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'imported', 'ignored', 'duplicate_skipped'
    imported_target_id INTEGER REFERENCES targets(id),
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Discovery templates for reusable configurations
CREATE TABLE IF NOT EXISTS discovery_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    discovery_type VARCHAR(50) NOT NULL,
    config JSONB NOT NULL,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_discovery_jobs_status ON discovery_jobs(status);
CREATE INDEX IF NOT EXISTS idx_discovery_jobs_created_by ON discovery_jobs(created_by);
CREATE INDEX IF NOT EXISTS idx_discovered_targets_job_id ON discovered_targets(discovery_job_id);
CREATE INDEX IF NOT EXISTS idx_discovered_targets_ip ON discovered_targets(ip_address);
CREATE INDEX IF NOT EXISTS idx_discovered_targets_import_status ON discovered_targets(import_status);
CREATE INDEX IF NOT EXISTS idx_discovered_targets_duplicate_status ON discovered_targets(duplicate_status);
CREATE INDEX IF NOT EXISTS idx_discovery_templates_type ON discovery_templates(discovery_type);
CREATE INDEX IF NOT EXISTS idx_discovery_templates_created_by ON discovery_templates(created_by);