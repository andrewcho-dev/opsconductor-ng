-- Phase 7.2: Enhanced Notifications Schema Updates
-- User notification preferences and multi-channel support

-- User notification preferences table
CREATE TABLE IF NOT EXISTS user_notification_preferences (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    email_enabled BOOLEAN NOT NULL DEFAULT true,
    email_address TEXT, -- Override user's primary email if needed
    webhook_enabled BOOLEAN NOT NULL DEFAULT false,
    webhook_url TEXT,
    slack_enabled BOOLEAN NOT NULL DEFAULT false,
    slack_webhook_url TEXT,
    slack_channel TEXT,
    teams_enabled BOOLEAN NOT NULL DEFAULT false,
    teams_webhook_url TEXT,
    notify_on_success BOOLEAN NOT NULL DEFAULT true,
    notify_on_failure BOOLEAN NOT NULL DEFAULT true,
    notify_on_start BOOLEAN NOT NULL DEFAULT false,
    quiet_hours_enabled BOOLEAN NOT NULL DEFAULT false,
    quiet_hours_start TIME,
    quiet_hours_end TIME,
    quiet_hours_timezone TEXT DEFAULT 'America/Los_Angeles',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(user_id)
);

-- Create indexes for user_notification_preferences
CREATE INDEX IF NOT EXISTS idx_user_notification_preferences_user_id ON user_notification_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_user_notification_preferences_email_enabled ON user_notification_preferences(email_enabled);
CREATE INDEX IF NOT EXISTS idx_user_notification_preferences_webhook_enabled ON user_notification_preferences(webhook_enabled);

-- Notification channels table for extensible channel management
CREATE TABLE IF NOT EXISTS notification_channels (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE, -- 'email', 'slack', 'teams', 'webhook', 'sms'
    display_name TEXT NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    configuration_schema JSONB, -- JSON schema for channel-specific config
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Insert default notification channels
INSERT INTO notification_channels (name, display_name, description, is_active, configuration_schema) VALUES
('email', 'Email', 'Email notifications via SMTP', true, '{"type": "object", "properties": {"email_address": {"type": "string", "format": "email"}}}'),
('webhook', 'Webhook', 'HTTP webhook notifications', true, '{"type": "object", "properties": {"webhook_url": {"type": "string", "format": "uri"}}}'),
('slack', 'Slack', 'Slack channel/DM notifications', true, '{"type": "object", "properties": {"webhook_url": {"type": "string", "format": "uri"}, "channel": {"type": "string"}}}'),
('teams', 'Microsoft Teams', 'Microsoft Teams channel notifications', true, '{"type": "object", "properties": {"webhook_url": {"type": "string", "format": "uri"}}}')
ON CONFLICT (name) DO NOTHING;

-- Notification rules table for advanced notification logic
CREATE TABLE IF NOT EXISTS notification_rules (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    conditions JSONB NOT NULL, -- JSON conditions for when to trigger
    channels TEXT[] NOT NULL, -- Array of channel names to notify
    escalation_delay_minutes INTEGER DEFAULT 0, -- Minutes to wait before escalation
    escalation_channels TEXT[], -- Channels to escalate to
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Create indexes for notification_rules
CREATE INDEX IF NOT EXISTS idx_notification_rules_user_id ON notification_rules(user_id);
CREATE INDEX IF NOT EXISTS idx_notification_rules_is_active ON notification_rules(is_active);
CREATE INDEX IF NOT EXISTS idx_notification_rules_conditions_gin ON notification_rules USING GIN(conditions);

-- Notification templates table for customizable message templates
CREATE TABLE IF NOT EXISTS notification_templates (
    id BIGSERIAL PRIMARY KEY,
    channel TEXT NOT NULL REFERENCES notification_channels(name),
    event_type TEXT NOT NULL, -- 'job_success', 'job_failure', 'job_start', etc.
    name TEXT NOT NULL,
    description TEXT,
    subject_template TEXT, -- For email/teams
    body_template TEXT NOT NULL, -- Jinja2 template
    is_default BOOLEAN NOT NULL DEFAULT false,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(channel, event_type, name)
);

-- Insert default notification templates
INSERT INTO notification_templates (channel, event_type, name, description, subject_template, body_template, is_default, is_active) VALUES
-- Email templates
('email', 'job_success', 'Default Success', 'Default job success email template', 
 'OpsConductor: Job {{ job_name }} - Success', 
 '<html><body><h2>Job Completed Successfully</h2><p>Your job <strong>{{ job_name }}</strong> has completed successfully.</p><h3>Job Details:</h3><ul><li><strong>Job ID:</strong> {{ job_id }}</li><li><strong>Run ID:</strong> {{ run_id }}</li><li><strong>Started:</strong> {{ started_at }}</li><li><strong>Finished:</strong> {{ finished_at }}</li><li><strong>Duration:</strong> {{ duration }}</li></ul>{% if steps_summary %}<h3>Steps Summary:</h3><ul><li>Total Steps: {{ steps_summary.total }}</li><li>Successful: {{ steps_summary.succeeded }}</li><li>Failed: {{ steps_summary.failed }}</li></ul>{% endif %}<p>You can view the full details in the OpsConductor dashboard.</p></body></html>', 
 true, true),
('email', 'job_failure', 'Default Failure', 'Default job failure email template',
 'OpsConductor: Job {{ job_name }} - Failed',
 '<html><body><h2 style="color: #d32f2f;">Job Failed</h2><p>Your job <strong>{{ job_name }}</strong> has failed.</p><h3>Job Details:</h3><ul><li><strong>Job ID:</strong> {{ job_id }}</li><li><strong>Run ID:</strong> {{ run_id }}</li><li><strong>Started:</strong> {{ started_at }}</li><li><strong>Failed:</strong> {{ finished_at }}</li><li><strong>Duration:</strong> {{ duration }}</li></ul>{% if steps_summary %}<h3>Steps Summary:</h3><ul><li>Total Steps: {{ steps_summary.total }}</li><li>Successful: {{ steps_summary.succeeded }}</li><li>Failed: {{ steps_summary.failed }}</li></ul>{% endif %}{% if error_details %}<h3>Error Details:</h3><pre style="background-color: #f5f5f5; padding: 10px; border-radius: 4px;">{{ error_details }}</pre>{% endif %}<p>Please check the OpsConductor dashboard for detailed error information.</p></body></html>',
 true, true),
-- Slack templates
('slack', 'job_success', 'Default Success', 'Default job success Slack template',
 null,
 '{"text": "✅ Job Completed Successfully", "blocks": [{"type": "section", "text": {"type": "mrkdwn", "text": "*Job {{ job_name }}* has completed successfully"}}, {"type": "section", "fields": [{"type": "mrkdwn", "text": "*Job ID:*\\n{{ job_id }}"}, {"type": "mrkdwn", "text": "*Run ID:*\\n{{ run_id }}"}, {"type": "mrkdwn", "text": "*Duration:*\\n{{ duration }}"}, {"type": "mrkdwn", "text": "*Status:*\\n:white_check_mark: Success"}]}]}',
 true, true),
('slack', 'job_failure', 'Default Failure', 'Default job failure Slack template',
 null,
 '{"text": "❌ Job Failed", "blocks": [{"type": "section", "text": {"type": "mrkdwn", "text": "*Job {{ job_name }}* has failed"}}, {"type": "section", "fields": [{"type": "mrkdwn", "text": "*Job ID:*\\n{{ job_id }}"}, {"type": "mrkdwn", "text": "*Run ID:*\\n{{ run_id }}"}, {"type": "mrkdwn", "text": "*Duration:*\\n{{ duration }}"}, {"type": "mrkdwn", "text": "*Status:*\\n:x: Failed"}]}{% if error_details %}, {"type": "section", "text": {"type": "mrkdwn", "text": "*Error Details:*\\n```{{ error_details }}```"}}{% endif %}]}',
 true, true),
-- Teams templates  
('teams', 'job_success', 'Default Success', 'Default job success Teams template',
 'Job Completed Successfully',
 '{"@type": "MessageCard", "@context": "http://schema.org/extensions", "themeColor": "00FF00", "summary": "Job {{ job_name }} completed successfully", "sections": [{"activityTitle": "Job Completed Successfully", "activitySubtitle": "{{ job_name }}", "facts": [{"name": "Job ID", "value": "{{ job_id }}"}, {"name": "Run ID", "value": "{{ run_id }}"}, {"name": "Duration", "value": "{{ duration }}"}, {"name": "Status", "value": "Success"}]}]}',
 true, true),
('teams', 'job_failure', 'Default Failure', 'Default job failure Teams template',
 'Job Failed',
 '{"@type": "MessageCard", "@context": "http://schema.org/extensions", "themeColor": "FF0000", "summary": "Job {{ job_name }} failed", "sections": [{"activityTitle": "Job Failed", "activitySubtitle": "{{ job_name }}", "facts": [{"name": "Job ID", "value": "{{ job_id }}"}, {"name": "Run ID", "value": "{{ run_id }}"}, {"name": "Duration", "value": "{{ duration }}"}, {"name": "Status", "value": "Failed"}]{% if error_details %}, "text": "**Error Details:**\\n{{ error_details }}"{% endif %}}]}',
 true, true),
-- Webhook templates
('webhook', 'job_success', 'Default Success', 'Default job success webhook template',
 null,
 '{"event": "job_success", "job_id": {{ job_id }}, "run_id": {{ run_id }}, "job_name": "{{ job_name }}", "status": "{{ status }}", "started_at": "{{ started_at }}", "finished_at": "{{ finished_at }}", "duration": "{{ duration }}"{% if steps_summary %}, "steps_summary": {{ steps_summary | tojson }}{% endif %}}',
 true, true),
('webhook', 'job_failure', 'Default Failure', 'Default job failure webhook template',
 null,
 '{"event": "job_failure", "job_id": {{ job_id }}, "run_id": {{ run_id }}, "job_name": "{{ job_name }}", "status": "{{ status }}", "started_at": "{{ started_at }}", "finished_at": "{{ finished_at }}", "duration": "{{ duration }}"{% if steps_summary %}, "steps_summary": {{ steps_summary | tojson }}{% endif %}{% if error_details %}, "error_details": "{{ error_details }}"{% endif %}}',
 true, true)
ON CONFLICT (channel, event_type, name) DO NOTHING;

-- Update notifications table to support new channels
ALTER TABLE notifications DROP CONSTRAINT IF EXISTS notifications_channel_check;
ALTER TABLE notifications ADD CONSTRAINT notifications_channel_check 
    CHECK (channel IN ('webhook', 'email', 'slack', 'teams', 'sms'));

-- Add template reference to notifications
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS template_id BIGINT REFERENCES notification_templates(id);
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS user_id BIGINT REFERENCES users(id);

-- Create indexes for new columns
CREATE INDEX IF NOT EXISTS idx_notifications_template_id ON notifications(template_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);

-- Add escalation tracking
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS is_escalation BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS parent_notification_id BIGINT REFERENCES notifications(id);
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS escalation_level INTEGER NOT NULL DEFAULT 0;

-- Create indexes for escalation
CREATE INDEX IF NOT EXISTS idx_notifications_is_escalation ON notifications(is_escalation);
CREATE INDEX IF NOT EXISTS idx_notifications_parent_notification_id ON notifications(parent_notification_id);

-- Create a view for notification preferences with user details
CREATE OR REPLACE VIEW user_notification_preferences_view AS
SELECT 
    u.id as user_id,
    u.email as user_email,
    u.username,
    u.role,
    COALESCE(unp.email_enabled, true) as email_enabled,
    COALESCE(unp.email_address, u.email) as notification_email,
    COALESCE(unp.webhook_enabled, false) as webhook_enabled,
    unp.webhook_url,
    COALESCE(unp.slack_enabled, false) as slack_enabled,
    unp.slack_webhook_url,
    unp.slack_channel,
    COALESCE(unp.teams_enabled, false) as teams_enabled,
    unp.teams_webhook_url,
    COALESCE(unp.notify_on_success, true) as notify_on_success,
    COALESCE(unp.notify_on_failure, true) as notify_on_failure,
    COALESCE(unp.notify_on_start, false) as notify_on_start,
    COALESCE(unp.quiet_hours_enabled, false) as quiet_hours_enabled,
    unp.quiet_hours_start,
    unp.quiet_hours_end,
    COALESCE(unp.quiet_hours_timezone, 'America/Los_Angeles') as quiet_hours_timezone,
    unp.created_at as preferences_created_at,
    unp.updated_at as preferences_updated_at
FROM users u
LEFT JOIN user_notification_preferences unp ON u.id = unp.user_id;

-- Add comments for documentation
COMMENT ON TABLE user_notification_preferences IS 'User-specific notification preferences and channel configurations';
COMMENT ON TABLE notification_channels IS 'Available notification channels with configuration schemas';
COMMENT ON TABLE notification_rules IS 'Advanced notification rules with conditions and escalation';
COMMENT ON TABLE notification_templates IS 'Customizable notification message templates for different channels';
COMMENT ON VIEW user_notification_preferences_view IS 'Combined view of users and their notification preferences with defaults';

-- Performance optimization
ANALYZE user_notification_preferences;
ANALYZE notification_channels;
ANALYZE notification_rules;
ANALYZE notification_templates;