-- Phase 3 Communication Service Migration
-- Add notification preferences and SMTP settings tables

-- Notification preferences table
CREATE TABLE IF NOT EXISTS communication.notification_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES identity.users(id) ON DELETE CASCADE,
    email_enabled BOOLEAN DEFAULT true,
    sms_enabled BOOLEAN DEFAULT false,
    push_enabled BOOLEAN DEFAULT true,
    job_success_notifications BOOLEAN DEFAULT true,
    job_failure_notifications BOOLEAN DEFAULT true,
    system_alerts BOOLEAN DEFAULT true,
    maintenance_notifications BOOLEAN DEFAULT true,
    email_frequency VARCHAR(20) DEFAULT 'immediate' CHECK (email_frequency IN ('immediate', 'daily', 'weekly')),
    quiet_hours_start TIME,
    quiet_hours_end TIME,
    timezone VARCHAR(50) DEFAULT 'UTC',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

-- SMTP settings table
CREATE TABLE IF NOT EXISTS communication.smtp_settings (
    id SERIAL PRIMARY KEY,
    host VARCHAR(255) NOT NULL,
    port INTEGER NOT NULL DEFAULT 587,
    username VARCHAR(255),
    password VARCHAR(255),
    use_tls BOOLEAN DEFAULT true,
    use_ssl BOOLEAN DEFAULT false,
    from_email VARCHAR(255) NOT NULL,
    from_name VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_notification_preferences_user_id ON communication.notification_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_smtp_settings_active ON communication.smtp_settings(is_active);

-- Insert default notification preferences for existing users
INSERT INTO communication.notification_preferences (user_id)
SELECT id FROM identity.users 
WHERE id NOT IN (SELECT user_id FROM communication.notification_preferences);

COMMIT;