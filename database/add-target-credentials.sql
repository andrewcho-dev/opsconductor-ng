-- Add target credentials table for secure credential storage
-- This extends the assets schema with encrypted credential management

-- Create target_credentials table
CREATE TABLE IF NOT EXISTS assets.target_credentials (
    id SERIAL PRIMARY KEY,
    target_id INTEGER NOT NULL REFERENCES assets.targets(id) ON DELETE CASCADE,
    encrypted_credentials TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure one credential set per target
    UNIQUE(target_id)
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_target_credentials_target_id ON assets.target_credentials(target_id);

-- Add comments
COMMENT ON TABLE assets.target_credentials IS 'Stores encrypted credentials for target servers';
COMMENT ON COLUMN assets.target_credentials.target_id IS 'Reference to the target server';
COMMENT ON COLUMN assets.target_credentials.encrypted_credentials IS 'Encrypted JSON containing username and password';

-- Grant permissions to automation service
GRANT SELECT, INSERT, UPDATE, DELETE ON assets.target_credentials TO postgres;
GRANT USAGE, SELECT ON SEQUENCE assets.target_credentials_id_seq TO postgres;

-- Insert some demo credentials for testing (these would be set via API in production)
-- Note: These are encrypted with a demo key and should not be used in production

INSERT INTO assets.target_credentials (target_id, encrypted_credentials) VALUES 
(1, 'gAAAAABhkJ9X...demo_encrypted_credentials_1'),
(2, 'gAAAAABhkJ9Y...demo_encrypted_credentials_2'),
(3, 'gAAAAABhkJ9Z...demo_encrypted_credentials_3')
ON CONFLICT (target_id) DO NOTHING;

-- Add audit trigger for credential changes
CREATE OR REPLACE FUNCTION assets.audit_credential_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO assets.audit_log (table_name, operation, record_id, changed_by, changed_at, changes)
        VALUES ('target_credentials', 'INSERT', NEW.id, current_user, NOW(), 
                json_build_object('target_id', NEW.target_id, 'action', 'credentials_added'));
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO assets.audit_log (table_name, operation, record_id, changed_by, changed_at, changes)
        VALUES ('target_credentials', 'UPDATE', NEW.id, current_user, NOW(),
                json_build_object('target_id', NEW.target_id, 'action', 'credentials_updated'));
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO assets.audit_log (table_name, operation, record_id, changed_by, changed_at, changes)
        VALUES ('target_credentials', 'DELETE', OLD.id, current_user, NOW(),
                json_build_object('target_id', OLD.target_id, 'action', 'credentials_removed'));
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create audit trigger (only if audit_log table exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'assets' AND table_name = 'audit_log') THEN
        DROP TRIGGER IF EXISTS audit_target_credentials ON assets.target_credentials;
        CREATE TRIGGER audit_target_credentials
            AFTER INSERT OR UPDATE OR DELETE ON assets.target_credentials
            FOR EACH ROW EXECUTE FUNCTION assets.audit_credential_changes();
    END IF;
END $$;