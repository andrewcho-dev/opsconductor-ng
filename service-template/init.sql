-- New Service Database Schema
-- Modify this file based on your service's data requirements

-- Main data table (example)
CREATE TABLE IF NOT EXISTS new_service_data (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_new_service_data_name ON new_service_data(name);
CREATE INDEX IF NOT EXISTS idx_new_service_data_status ON new_service_data(status);
CREATE INDEX IF NOT EXISTS idx_new_service_data_created_at ON new_service_data(created_at);
CREATE INDEX IF NOT EXISTS idx_new_service_data_metadata ON new_service_data USING GIN(metadata);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update updated_at
CREATE TRIGGER update_new_service_data_updated_at 
    BEFORE UPDATE ON new_service_data 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Sample data for testing
INSERT INTO new_service_data (name, description, metadata) VALUES 
('Sample Item 1', 'This is a sample item for testing', '{"category": "test", "priority": "high"}'),
('Sample Item 2', 'Another sample item', '{"category": "demo", "priority": "medium"}'),
('Sample Item 3', 'Third sample item', '{"category": "example", "priority": "low"}')
ON CONFLICT DO NOTHING;

-- Additional tables as needed for your service
-- Example: relationships, configurations, logs, etc.

-- Example: Service configuration table
CREATE TABLE IF NOT EXISTS service_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default configuration
INSERT INTO service_config (config_key, config_value, description) VALUES 
('max_items_per_page', '50', 'Maximum number of items to return per page'),
('default_status', 'active', 'Default status for new items'),
('enable_notifications', 'true', 'Whether to send notifications for events')
ON CONFLICT (config_key) DO NOTHING;

-- Example: Audit log table
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    record_id INTEGER NOT NULL,
    action VARCHAR(20) NOT NULL, -- INSERT, UPDATE, DELETE
    old_values JSONB,
    new_values JSONB,
    user_id INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for audit log
CREATE INDEX IF NOT EXISTS idx_audit_log_table_record ON audit_log(table_name, record_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id);

-- Grant permissions (adjust as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO newservice;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO newservice;