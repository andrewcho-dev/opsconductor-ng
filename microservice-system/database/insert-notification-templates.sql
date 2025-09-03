-- Insert default notification channels
INSERT INTO notification_channels (name, display_name, description, is_active, configuration_schema) VALUES
('email', 'Email', 'Email notifications via SMTP', true, '{"required": ["email_address"], "optional": []}'),
('slack', 'Slack', 'Slack notifications via webhook', true, '{"required": ["webhook_url"], "optional": ["channel"]}'),
('teams', 'Microsoft Teams', 'Microsoft Teams notifications via webhook', true, '{"required": ["webhook_url"], "optional": []}'),
('webhook', 'Generic Webhook', 'Generic HTTP webhook notifications', true, '{"required": ["webhook_url"], "optional": []}')
ON CONFLICT (name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    is_active = EXCLUDED.is_active,
    configuration_schema = EXCLUDED.configuration_schema;

-- Insert default email templates
INSERT INTO notification_templates (channel, event_type, name, description, subject_template, body_template, is_default, is_active) VALUES
-- Email templates
('email', 'job_success', 'Default Job Success Email', 'Default template for successful job completion', 
 '✅ Job "{{ job_name }}" completed successfully',
 '<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .header { background-color: #28a745; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; }
        .details { background-color: #f8f9fa; padding: 15px; border-left: 4px solid #28a745; margin: 15px 0; }
        .footer { background-color: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="header">
        <h1>✅ Job Completed Successfully</h1>
    </div>
    <div class="content">
        <p>Hello,</p>
        <p>Your job <strong>{{ job_name }}</strong> has completed successfully.</p>
        
        <div class="details">
            <h3>Job Details:</h3>
            <ul>
                <li><strong>Job Name:</strong> {{ job_name }}</li>
                <li><strong>Job ID:</strong> {{ job_id }}</li>
                <li><strong>Run ID:</strong> {{ run_id }}</li>
                <li><strong>Status:</strong> {{ status|title }}</li>
                <li><strong>Started:</strong> {{ started_at }}</li>
                <li><strong>Finished:</strong> {{ finished_at }}</li>
                <li><strong>Duration:</strong> {{ duration }}</li>
                <li><strong>Requested by:</strong> {{ requested_by }}</li>
            </ul>
        </div>
        
        {% if steps_summary %}
        <div class="details">
            <h3>Steps Summary:</h3>
            <ul>
                <li><strong>Total Steps:</strong> {{ steps_summary.total }}</li>
                <li><strong>Succeeded:</strong> {{ steps_summary.succeeded }}</li>
                <li><strong>Failed:</strong> {{ steps_summary.failed }}</li>
            </ul>
        </div>
        {% endif %}
    </div>
    <div class="footer">
        <p>This is an automated notification from OpsConductor.</p>
    </div>
</body>
</html>', true, true),

('email', 'job_failure', 'Default Job Failure Email', 'Default template for failed job completion',
 '❌ Job "{{ job_name }}" failed',
 '<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .header { background-color: #dc3545; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; }
        .details { background-color: #f8f9fa; padding: 15px; border-left: 4px solid #dc3545; margin: 15px 0; }
        .error { background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 10px; border-radius: 4px; margin: 10px 0; }
        .footer { background-color: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="header">
        <h1>❌ Job Failed</h1>
    </div>
    <div class="content">
        <p>Hello,</p>
        <p>Your job <strong>{{ job_name }}</strong> has failed and requires attention.</p>
        
        <div class="details">
            <h3>Job Details:</h3>
            <ul>
                <li><strong>Job Name:</strong> {{ job_name }}</li>
                <li><strong>Job ID:</strong> {{ job_id }}</li>
                <li><strong>Run ID:</strong> {{ run_id }}</li>
                <li><strong>Status:</strong> {{ status|title }}</li>
                <li><strong>Started:</strong> {{ started_at }}</li>
                <li><strong>Finished:</strong> {{ finished_at }}</li>
                <li><strong>Duration:</strong> {{ duration }}</li>
                <li><strong>Requested by:</strong> {{ requested_by }}</li>
            </ul>
        </div>
        
        {% if steps_summary %}
        <div class="details">
            <h3>Steps Summary:</h3>
            <ul>
                <li><strong>Total Steps:</strong> {{ steps_summary.total }}</li>
                <li><strong>Succeeded:</strong> {{ steps_summary.succeeded }}</li>
                <li><strong>Failed:</strong> {{ steps_summary.failed }}</li>
            </ul>
        </div>
        {% endif %}
        
        {% if error_details %}
        <div class="error">
            <h4>Error Details:</h4>
            <pre>{{ error_details }}</pre>
        </div>
        {% endif %}
    </div>
    <div class="footer">
        <p>This is an automated notification from OpsConductor.</p>
    </div>
</body>
</html>', true, true),

('email', 'job_start', 'Default Job Start Email', 'Default template for job start notification',
 '🚀 Job "{{ job_name }}" started',
 '<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .header { background-color: #007bff; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; }
        .details { background-color: #f8f9fa; padding: 15px; border-left: 4px solid #007bff; margin: 15px 0; }
        .footer { background-color: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Job Started</h1>
    </div>
    <div class="content">
        <p>Hello,</p>
        <p>Your job <strong>{{ job_name }}</strong> has started execution.</p>
        
        <div class="details">
            <h3>Job Details:</h3>
            <ul>
                <li><strong>Job Name:</strong> {{ job_name }}</li>
                <li><strong>Job ID:</strong> {{ job_id }}</li>
                <li><strong>Run ID:</strong> {{ run_id }}</li>
                <li><strong>Status:</strong> {{ status|title }}</li>
                <li><strong>Started:</strong> {{ started_at }}</li>
                <li><strong>Requested by:</strong> {{ requested_by }}</li>
            </ul>
        </div>
    </div>
    <div class="footer">
        <p>This is an automated notification from OpsConductor.</p>
    </div>
</body>
</html>', true, true),

-- Slack templates
('slack', 'job_success', 'Default Job Success Slack', 'Default Slack template for successful job completion', null,
 '{
    "text": "✅ Job completed successfully",
    "blocks": [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "✅ Job Completed Successfully"
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": "*Job Name:*\n{{ job_name }}"
                },
                {
                    "type": "mrkdwn",
                    "text": "*Status:*\n{{ status|title }}"
                },
                {
                    "type": "mrkdwn",
                    "text": "*Duration:*\n{{ duration }}"
                },
                {
                    "type": "mrkdwn",
                    "text": "*Requested by:*\n{{ requested_by }}"
                }
            ]
        }
    ]
}', true, true),

('slack', 'job_failure', 'Default Job Failure Slack', 'Default Slack template for failed job completion', null,
 '{
    "text": "❌ Job failed",
    "blocks": [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "❌ Job Failed"
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": "*Job Name:*\n{{ job_name }}"
                },
                {
                    "type": "mrkdwn",
                    "text": "*Status:*\n{{ status|title }}"
                },
                {
                    "type": "mrkdwn",
                    "text": "*Duration:*\n{{ duration }}"
                },
                {
                    "type": "mrkdwn",
                    "text": "*Requested by:*\n{{ requested_by }}"
                }
            ]
        }{% if error_details %},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Error Details:*\n```{{ error_details }}```"
            }
        }{% endif %}
    ]
}', true, true),

-- Teams templates
('teams', 'job_success', 'Default Job Success Teams', 'Default Teams template for successful job completion', null,
 '{
    "@type": "MessageCard",
    "@context": "http://schema.org/extensions",
    "themeColor": "00FF00",
    "summary": "Job {{ job_name }} completed successfully",
    "sections": [{
        "activityTitle": "✅ Job Completed Successfully",
        "activitySubtitle": "{{ job_name }}",
        "facts": [
            {"name": "Job ID", "value": "{{ job_id }}"},
            {"name": "Status", "value": "{{ status|title }}"},
            {"name": "Duration", "value": "{{ duration }}"},
            {"name": "Requested by", "value": "{{ requested_by }}"}
        ]
    }]
}', true, true),

('teams', 'job_failure', 'Default Job Failure Teams', 'Default Teams template for failed job completion', null,
 '{
    "@type": "MessageCard",
    "@context": "http://schema.org/extensions",
    "themeColor": "FF0000",
    "summary": "Job {{ job_name }} failed",
    "sections": [{
        "activityTitle": "❌ Job Failed",
        "activitySubtitle": "{{ job_name }}",
        "facts": [
            {"name": "Job ID", "value": "{{ job_id }}"},
            {"name": "Status", "value": "{{ status|title }}"},
            {"name": "Duration", "value": "{{ duration }}"},
            {"name": "Requested by", "value": "{{ requested_by }}"}{% if error_details %},
            {"name": "Error", "value": "{{ error_details }}"}{% endif %}
        ]
    }]
}', true, true)

ON CONFLICT (channel, event_type, name) DO UPDATE SET
    description = EXCLUDED.description,
    subject_template = EXCLUDED.subject_template,
    body_template = EXCLUDED.body_template,
    is_default = EXCLUDED.is_default,
    is_active = EXCLUDED.is_active,
    updated_at = CURRENT_TIMESTAMP;