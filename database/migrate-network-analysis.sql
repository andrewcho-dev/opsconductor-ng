-- Migration script to add Network Analysis schema to existing OpsConductor database
-- Run this script if you have an existing OpsConductor installation

BEGIN;

-- Create network analysis schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS network_analysis;

-- Remote Probes Table
CREATE TABLE IF NOT EXISTS network_analysis.remote_probes (
    id SERIAL PRIMARY KEY,
    probe_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    ip_address VARCHAR(45),
    hostname VARCHAR(255),
    os_type VARCHAR(50),
    version VARCHAR(100),
    capabilities JSONB DEFAULT '[]',
    interfaces JSONB DEFAULT '[]',
    status VARCHAR(50) DEFAULT 'active',
    registered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_heartbeat TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Capture Sessions Table
CREATE TABLE IF NOT EXISTS network_analysis.capture_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    probe_id VARCHAR(255) REFERENCES network_analysis.remote_probes(probe_id),
    user_id INTEGER,
    interface_name VARCHAR(100),
    filter_expression TEXT,
    duration INTEGER,
    packet_count INTEGER,
    status VARCHAR(50) DEFAULT 'starting',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    configuration JSONB DEFAULT '{}',
    results_summary JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Capture Results Table
CREATE TABLE IF NOT EXISTS network_analysis.capture_results (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) REFERENCES network_analysis.capture_sessions(session_id),
    probe_id VARCHAR(255) REFERENCES network_analysis.remote_probes(probe_id),
    packet_data JSONB,
    statistics JSONB DEFAULT '{}',
    ai_analysis JSONB DEFAULT '{}',
    file_path TEXT,
    file_size BIGINT,
    packet_count INTEGER DEFAULT 0,
    bytes_captured BIGINT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Network Monitoring Data Table
CREATE TABLE IF NOT EXISTS network_analysis.monitoring_data (
    id SERIAL PRIMARY KEY,
    probe_id VARCHAR(255) REFERENCES network_analysis.remote_probes(probe_id),
    interface_name VARCHAR(100),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    rx_bytes BIGINT DEFAULT 0,
    tx_bytes BIGINT DEFAULT 0,
    rx_packets BIGINT DEFAULT 0,
    tx_packets BIGINT DEFAULT 0,
    rx_errors BIGINT DEFAULT 0,
    tx_errors BIGINT DEFAULT 0,
    bandwidth_utilization FLOAT,
    latency_ms FLOAT,
    packet_loss_rate FLOAT,
    active_connections INTEGER,
    metrics JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Network Alerts Table
CREATE TABLE IF NOT EXISTS network_analysis.network_alerts (
    id SERIAL PRIMARY KEY,
    alert_id VARCHAR(255) UNIQUE NOT NULL,
    probe_id VARCHAR(255) REFERENCES network_analysis.remote_probes(probe_id),
    alert_type VARCHAR(100) NOT NULL,
    severity VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    source VARCHAR(255),
    interface_name VARCHAR(100),
    threshold_value FLOAT,
    current_value FLOAT,
    status VARCHAR(50) DEFAULT 'active',
    resolved BOOLEAN DEFAULT false,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by INTEGER,
    resolution_notes TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Analysis Jobs Table
CREATE TABLE IF NOT EXISTS network_analysis.analysis_jobs (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(255) UNIQUE NOT NULL,
    probe_id VARCHAR(255) REFERENCES network_analysis.remote_probes(probe_id),
    user_id INTEGER,
    job_type VARCHAR(100) NOT NULL,
    parameters JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'pending',
    priority INTEGER DEFAULT 5,
    scheduled_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    results JSONB DEFAULT '{}',
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Protocol Analysis Results Table
CREATE TABLE IF NOT EXISTS network_analysis.protocol_analysis (
    id SERIAL PRIMARY KEY,
    analysis_id VARCHAR(255) UNIQUE NOT NULL,
    session_id VARCHAR(255) REFERENCES network_analysis.capture_sessions(session_id),
    probe_id VARCHAR(255) REFERENCES network_analysis.remote_probes(probe_id),
    protocol VARCHAR(50) NOT NULL,
    analysis_results JSONB DEFAULT '{}',
    statistics JSONB DEFAULT '{}',
    recommendations JSONB DEFAULT '[]',
    anomalies JSONB DEFAULT '[]',
    performance_metrics JSONB DEFAULT '{}',
    security_findings JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- AI Analysis Results Table
CREATE TABLE IF NOT EXISTS network_analysis.ai_analysis (
    id SERIAL PRIMARY KEY,
    analysis_id VARCHAR(255) UNIQUE NOT NULL,
    session_id VARCHAR(255) REFERENCES network_analysis.capture_sessions(session_id),
    probe_id VARCHAR(255) REFERENCES network_analysis.remote_probes(probe_id),
    analysis_type VARCHAR(100) NOT NULL,
    confidence_score FLOAT CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    findings JSONB DEFAULT '[]',
    recommendations JSONB DEFAULT '[]',
    anomalies_detected JSONB DEFAULT '[]',
    performance_insights JSONB DEFAULT '{}',
    security_concerns JSONB DEFAULT '[]',
    root_cause_analysis JSONB DEFAULT '{}',
    remediation_plan JSONB DEFAULT '{}',
    supporting_evidence JSONB DEFAULT '[]',
    model_version VARCHAR(100),
    processing_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_remote_probes_probe_id ON network_analysis.remote_probes(probe_id);
CREATE INDEX IF NOT EXISTS idx_remote_probes_status ON network_analysis.remote_probes(status);
CREATE INDEX IF NOT EXISTS idx_remote_probes_last_heartbeat ON network_analysis.remote_probes(last_heartbeat);

CREATE INDEX IF NOT EXISTS idx_capture_sessions_session_id ON network_analysis.capture_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_capture_sessions_probe_id ON network_analysis.capture_sessions(probe_id);
CREATE INDEX IF NOT EXISTS idx_capture_sessions_status ON network_analysis.capture_sessions(status);
CREATE INDEX IF NOT EXISTS idx_capture_sessions_started_at ON network_analysis.capture_sessions(started_at);

CREATE INDEX IF NOT EXISTS idx_capture_results_session_id ON network_analysis.capture_results(session_id);
CREATE INDEX IF NOT EXISTS idx_capture_results_probe_id ON network_analysis.capture_results(probe_id);

CREATE INDEX IF NOT EXISTS idx_monitoring_data_probe_id ON network_analysis.monitoring_data(probe_id);
CREATE INDEX IF NOT EXISTS idx_monitoring_data_timestamp ON network_analysis.monitoring_data(timestamp);
CREATE INDEX IF NOT EXISTS idx_monitoring_data_interface ON network_analysis.monitoring_data(interface_name);

CREATE INDEX IF NOT EXISTS idx_network_alerts_probe_id ON network_analysis.network_alerts(probe_id);
CREATE INDEX IF NOT EXISTS idx_network_alerts_status ON network_analysis.network_alerts(status);
CREATE INDEX IF NOT EXISTS idx_network_alerts_severity ON network_analysis.network_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_network_alerts_created_at ON network_analysis.network_alerts(created_at);

CREATE INDEX IF NOT EXISTS idx_analysis_jobs_probe_id ON network_analysis.analysis_jobs(probe_id);
CREATE INDEX IF NOT EXISTS idx_analysis_jobs_status ON network_analysis.analysis_jobs(status);
CREATE INDEX IF NOT EXISTS idx_analysis_jobs_scheduled_at ON network_analysis.analysis_jobs(scheduled_at);

-- Update timestamp trigger function (should already exist)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at columns
DROP TRIGGER IF EXISTS trigger_remote_probes_updated_at ON network_analysis.remote_probes;
CREATE TRIGGER trigger_remote_probes_updated_at
    BEFORE UPDATE ON network_analysis.remote_probes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trigger_capture_sessions_updated_at ON network_analysis.capture_sessions;
CREATE TRIGGER trigger_capture_sessions_updated_at
    BEFORE UPDATE ON network_analysis.capture_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trigger_network_alerts_updated_at ON network_analysis.network_alerts;
CREATE TRIGGER trigger_network_alerts_updated_at
    BEFORE UPDATE ON network_analysis.network_alerts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trigger_analysis_jobs_updated_at ON network_analysis.analysis_jobs;
CREATE TRIGGER trigger_analysis_jobs_updated_at
    BEFORE UPDATE ON network_analysis.analysis_jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Views for common queries
CREATE OR REPLACE VIEW network_analysis.active_probes AS
SELECT 
    probe_id,
    name,
    location,
    ip_address,
    status,
    last_heartbeat,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - last_heartbeat)) AS seconds_since_heartbeat,
    CASE 
        WHEN EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - last_heartbeat)) < 300 THEN 'online'
        WHEN EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - last_heartbeat)) < 900 THEN 'warning'
        ELSE 'offline'
    END AS connection_status,
    interfaces,
    capabilities
FROM network_analysis.remote_probes
WHERE status = 'active';

CREATE OR REPLACE VIEW network_analysis.recent_captures AS
SELECT 
    cs.session_id,
    cs.probe_id,
    rp.name AS probe_name,
    rp.location AS probe_location,
    cs.interface_name,
    cs.status,
    cs.started_at,
    cs.completed_at,
    cr.packet_count,
    cr.bytes_captured,
    EXTRACT(EPOCH FROM (cs.completed_at - cs.started_at)) AS duration_seconds
FROM network_analysis.capture_sessions cs
LEFT JOIN network_analysis.remote_probes rp ON cs.probe_id = rp.probe_id
LEFT JOIN network_analysis.capture_results cr ON cs.session_id = cr.session_id
WHERE cs.started_at > CURRENT_TIMESTAMP - INTERVAL '24 hours'
ORDER BY cs.started_at DESC;

CREATE OR REPLACE VIEW network_analysis.alert_summary AS
SELECT 
    probe_id,
    alert_type,
    severity,
    COUNT(*) as alert_count,
    MAX(created_at) as latest_alert,
    COUNT(CASE WHEN resolved = false THEN 1 END) as active_alerts
FROM network_analysis.network_alerts
WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '24 hours'
GROUP BY probe_id, alert_type, severity
ORDER BY alert_count DESC;

-- Update role permissions to include network analysis permissions
UPDATE identity.roles 
SET permissions = permissions || '["network:probe:register", "network:probe:manage"]'::jsonb
WHERE name = 'admin';

UPDATE identity.roles 
SET permissions = permissions || '["network:probe:register"]'::jsonb
WHERE name = 'operator';

COMMIT;

-- Display success message
SELECT 'Network Analysis schema migration completed successfully!' as status;