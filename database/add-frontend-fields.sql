-- Migration to add missing frontend fields to assets table
-- This adds all the fields that the frontend AssetSpreadsheetForm expects

-- Add Device/Hardware Information
ALTER TABLE assets.assets ADD COLUMN IF NOT EXISTS device_type VARCHAR(50) DEFAULT 'other';
ALTER TABLE assets.assets ADD COLUMN IF NOT EXISTS hardware_make VARCHAR(100);
ALTER TABLE assets.assets ADD COLUMN IF NOT EXISTS hardware_model VARCHAR(100);
ALTER TABLE assets.assets ADD COLUMN IF NOT EXISTS serial_number VARCHAR(100);

-- Add Location Information
ALTER TABLE assets.assets ADD COLUMN IF NOT EXISTS physical_address TEXT;
ALTER TABLE assets.assets ADD COLUMN IF NOT EXISTS data_center VARCHAR(100);
ALTER TABLE assets.assets ADD COLUMN IF NOT EXISTS building VARCHAR(100);
ALTER TABLE assets.assets ADD COLUMN IF NOT EXISTS room VARCHAR(100);
ALTER TABLE assets.assets ADD COLUMN IF NOT EXISTS rack_position VARCHAR(100);
ALTER TABLE assets.assets ADD COLUMN IF NOT EXISTS rack_location VARCHAR(100);
ALTER TABLE assets.assets ADD COLUMN IF NOT EXISTS gps_coordinates VARCHAR(50);

-- Add Status and Management Information
ALTER TABLE assets.assets ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'active';
ALTER TABLE assets.assets ADD COLUMN IF NOT EXISTS environment VARCHAR(50) DEFAULT 'production';
ALTER TABLE assets.assets ADD COLUMN IF NOT EXISTS criticality VARCHAR(50) DEFAULT 'medium';
ALTER TABLE assets.assets ADD COLUMN IF NOT EXISTS owner VARCHAR(255);
ALTER TABLE assets.assets ADD COLUMN IF NOT EXISTS support_contact VARCHAR(255);
ALTER TABLE assets.assets ADD COLUMN IF NOT EXISTS contract_number VARCHAR(100);

-- Add Database-specific fields
ALTER TABLE assets.assets ADD COLUMN IF NOT EXISTS database_type VARCHAR(50);
ALTER TABLE assets.assets ADD COLUMN IF NOT EXISTS database_name VARCHAR(255);

-- Add Secondary Service fields
ALTER TABLE assets.assets ADD COLUMN IF NOT EXISTS secondary_service_type VARCHAR(50) DEFAULT 'none';
ALTER TABLE assets.assets ADD COLUMN IF NOT EXISTS secondary_port INTEGER;
ALTER TABLE assets.assets ADD COLUMN IF NOT EXISTS ftp_type VARCHAR(20);
ALTER TABLE assets.assets ADD COLUMN IF NOT EXISTS secondary_username VARCHAR(255);
ALTER TABLE assets.assets ADD COLUMN IF NOT EXISTS secondary_password_encrypted TEXT;

-- Add comments for field documentation
COMMENT ON COLUMN assets.assets.device_type IS 'Type of device: server, workstation, router, switch, firewall, database, web-server, application-server, storage, other';
COMMENT ON COLUMN assets.assets.status IS 'Asset status: active, inactive, maintenance, decommissioned';
COMMENT ON COLUMN assets.assets.environment IS 'Environment: production, staging, development, testing, qa';
COMMENT ON COLUMN assets.assets.criticality IS 'Business criticality: low, medium, high, critical';
COMMENT ON COLUMN assets.assets.secondary_service_type IS 'Secondary service: none, telnet, ftp_sftp';
COMMENT ON COLUMN assets.assets.ftp_type IS 'FTP protocol type: ftp, ftps, sftp (when secondary_service_type=ftp_sftp)';

-- Create indexes for commonly queried fields
CREATE INDEX IF NOT EXISTS idx_assets_device_type ON assets.assets(device_type);
CREATE INDEX IF NOT EXISTS idx_assets_status ON assets.assets(status);
CREATE INDEX IF NOT EXISTS idx_assets_environment ON assets.assets(environment);
CREATE INDEX IF NOT EXISTS idx_assets_criticality ON assets.assets(criticality);
CREATE INDEX IF NOT EXISTS idx_assets_data_center ON assets.assets(data_center);
CREATE INDEX IF NOT EXISTS idx_assets_owner ON assets.assets(owner);