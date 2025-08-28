-- Phase 9.1: HTTP/HTTPS Step Types Implementation
-- Add support for HTTP operations in job execution

-- HTTP request tracking table
CREATE TABLE IF NOT EXISTS http_requests (
    id BIGSERIAL PRIMARY KEY,
    job_run_step_id BIGINT NOT NULL REFERENCES job_run_steps(id) ON DELETE CASCADE,
    method VARCHAR(10) NOT NULL CHECK (method IN ('GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS')),
    url TEXT NOT NULL,
    request_headers JSONB DEFAULT '{}',
    request_body TEXT,
    response_status_code INTEGER,
    response_headers JSONB DEFAULT '{}',
    response_body TEXT,
    response_time_ms INTEGER,
    ssl_verify BOOLEAN DEFAULT true,
    timeout_seconds INTEGER DEFAULT 30,
    max_redirects INTEGER DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_http_requests_job_run_step_id ON http_requests(job_run_step_id);
CREATE INDEX IF NOT EXISTS idx_http_requests_method ON http_requests(method);
CREATE INDEX IF NOT EXISTS idx_http_requests_status_code ON http_requests(response_status_code);
CREATE INDEX IF NOT EXISTS idx_http_requests_created_at ON http_requests(created_at);

-- Webhook execution tracking
CREATE TABLE IF NOT EXISTS webhook_executions (
    id BIGSERIAL PRIMARY KEY,
    job_run_step_id BIGINT NOT NULL REFERENCES job_run_steps(id) ON DELETE CASCADE,
    webhook_url TEXT NOT NULL,
    payload JSONB NOT NULL,
    signature_method VARCHAR(20), -- 'hmac-sha256', 'hmac-sha1', etc.
    signature_header VARCHAR(100), -- 'X-Hub-Signature-256', etc.
    signature_value TEXT,
    response_status_code INTEGER,
    response_body TEXT,
    response_time_ms INTEGER,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    next_retry_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Indexes for webhook tracking
CREATE INDEX IF NOT EXISTS idx_webhook_executions_job_run_step_id ON webhook_executions(job_run_step_id);
CREATE INDEX IF NOT EXISTS idx_webhook_executions_status ON webhook_executions(response_status_code);
CREATE INDEX IF NOT EXISTS idx_webhook_executions_retry ON webhook_executions(next_retry_at) WHERE next_retry_at IS NOT NULL;

-- HTTP authentication configurations (extends credentials table)
ALTER TABLE credentials ADD COLUMN IF NOT EXISTS auth_type VARCHAR(20) DEFAULT 'none' 
    CHECK (auth_type IN ('none', 'basic', 'bearer', 'api_key', 'oauth2', 'digest', 'ntlm'));
ALTER TABLE credentials ADD COLUMN IF NOT EXISTS auth_config JSONB DEFAULT '{}';

-- HTTP job templates for common operations
INSERT INTO jobs (name, version, definition, is_active, created_by) VALUES
('HTTP API Health Check', 1, '{
  "name": "HTTP API Health Check",
  "version": 1,
  "parameters": {
    "api_url": "https://api.example.com/health",
    "expected_status": 200,
    "timeout": 30
  },
  "steps": [
    {
      "type": "http.get",
      "name": "Check API Health",
      "url": "{{ api_url }}",
      "timeout_sec": "{{ timeout }}",
      "expected_status": "{{ expected_status }}",
      "headers": {
        "User-Agent": "OpsConductor-HealthCheck/1.0"
      }
    }
  ]
}', true, 1),
('REST API Data Sync', 1, '{
  "name": "REST API Data Sync",
  "version": 1,
  "parameters": {
    "source_api": "https://source.example.com/api/data",
    "target_api": "https://target.example.com/api/data",
    "auth_token": "bearer_token_here"
  },
  "steps": [
    {
      "type": "http.get",
      "name": "Fetch Source Data",
      "url": "{{ source_api }}",
      "auth_type": "bearer",
      "auth_token": "{{ auth_token }}",
      "timeout_sec": 60
    },
    {
      "type": "http.post",
      "name": "Send to Target",
      "url": "{{ target_api }}",
      "auth_type": "bearer", 
      "auth_token": "{{ auth_token }}",
      "body": "{{ steps[0].response_body }}",
      "headers": {
        "Content-Type": "application/json"
      },
      "timeout_sec": 60
    }
  ]
}', true, 1),
('Webhook Notification', 1, '{
  "name": "Webhook Notification",
  "version": 1,
  "parameters": {
    "webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
    "message": "Job completed successfully",
    "channel": "#alerts"
  },
  "steps": [
    {
      "type": "webhook.call",
      "name": "Send Webhook",
      "url": "{{ webhook_url }}",
      "payload": {
        "text": "{{ message }}",
        "channel": "{{ channel }}",
        "username": "OpsConductor",
        "timestamp": "{{ current_timestamp }}"
      },
      "signature_method": "hmac-sha256",
      "timeout_sec": 30
    }
  ]
}', true, 1);

-- Add comments for documentation
COMMENT ON TABLE http_requests IS 'HTTP request execution tracking and response storage';
COMMENT ON TABLE webhook_executions IS 'Webhook execution tracking with retry logic';
COMMENT ON COLUMN credentials.auth_type IS 'HTTP authentication method type';
COMMENT ON COLUMN credentials.auth_config IS 'HTTP authentication configuration (tokens, keys, etc.)';

-- Performance optimization
ANALYZE http_requests;
ANALYZE webhook_executions;