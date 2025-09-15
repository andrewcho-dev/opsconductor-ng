import React, { useState, useEffect } from 'react';
import { communicationApi } from '../services/api';
import { WebhookSettings as WebhookSettingsType, CommunicationTestRequest } from '../types';
import { Globe, Send, AlertCircle, CheckCircle, Plus, Trash2 } from 'lucide-react';

const WebhookSettings: React.FC = () => {
  const [settings, setSettings] = useState<WebhookSettingsType>({
    url: '',
    method: 'POST',
    headers: {},
    auth_type: 'none',
    auth_config: {},
    payload_template: '{"message": "{{message}}", "timestamp": "{{timestamp}}"}',
    content_type: 'application/json'
  });
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [testMessage, setTestMessage] = useState('This is a test message from OpsConductor!');
  const [newHeaderKey, setNewHeaderKey] = useState('');
  const [newHeaderValue, setNewHeaderValue] = useState('');

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    setIsLoading(true);
    try {
      const channel = await communicationApi.getChannelByType('webhook');
      if (channel) {
        setSettings(channel.configuration as WebhookSettingsType);
      }
    } catch (error) {
      console.error('Failed to load Webhook settings:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    setMessage(null);
    try {
      await communicationApi.saveChannel({
        name: 'Generic Webhook',
        channel_type: 'webhook',
        configuration: settings,
        is_active: true
      });
      setMessage({ type: 'success', text: 'Webhook settings saved successfully!' });
    } catch (error: any) {
      setMessage({ type: 'error', text: error.message || 'Failed to save Webhook settings' });
    } finally {
      setIsSaving(false);
    }
  };

  const handleTest = async () => {
    if (!settings.url) {
      setMessage({ type: 'error', text: 'Please configure webhook URL before testing' });
      return;
    }

    setIsTesting(true);
    setMessage(null);
    try {
      const testRequest: CommunicationTestRequest = {
        channel_type: 'webhook',
        test_message: testMessage
      };
      const result = await communicationApi.testChannel('webhook', testRequest);
      setMessage({ 
        type: result.success ? 'success' : 'error', 
        text: result.message 
      });
    } catch (error: any) {
      setMessage({ type: 'error', text: error.message || 'Failed to test Webhook configuration' });
    } finally {
      setIsTesting(false);
    }
  };

  const addHeader = () => {
    if (newHeaderKey && newHeaderValue) {
      setSettings({
        ...settings,
        headers: {
          ...settings.headers,
          [newHeaderKey]: newHeaderValue
        }
      });
      setNewHeaderKey('');
      setNewHeaderValue('');
    }
  };

  const removeHeader = (key: string) => {
    const newHeaders = { ...settings.headers };
    delete newHeaders[key];
    setSettings({ ...settings, headers: newHeaders });
  };

  const updateAuthConfig = (key: string, value: string) => {
    setSettings({
      ...settings,
      auth_config: {
        ...settings.auth_config,
        [key]: value
      }
    });
  };

  if (isLoading) {
    return <div style={{ padding: '20px', textAlign: 'center' }}>Loading Webhook settings...</div>;
  }

  return (
    <div className="webhook-settings">
      <style>
        {`
          .webhook-settings {
            max-width: 800px;
          }
          .form-group {
            margin-bottom: 16px;
          }
          .form-label {
            display: block;
            font-weight: 500;
            margin-bottom: 4px;
            color: var(--neutral-700);
            font-size: 13px;
          }
          .form-input, .form-select {
            width: 100%;
            padding: 8px 12px;
            border: 1px solid var(--neutral-300);
            border-radius: 4px;
            font-size: 13px;
            transition: border-color 0.15s;
          }
          .form-input:focus, .form-select:focus {
            outline: none;
            border-color: var(--primary-blue);
            box-shadow: 0 0 0 2px var(--primary-blue-light);
          }
          .form-textarea {
            min-height: 100px;
            resize: vertical;
            font-family: 'Courier New', monospace;
          }
          .form-help {
            font-size: 11px;
            color: var(--neutral-500);
            margin-top: 4px;
            line-height: 1.4;
          }
          .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
          }
          .button-group {
            display: flex;
            gap: 8px;
            margin-top: 20px;
          }
          .btn {
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            font-size: 13px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.15s;
            display: flex;
            align-items: center;
            gap: 6px;
          }
          .btn-primary {
            background: var(--primary-blue);
            color: white;
          }
          .btn-primary:hover:not(:disabled) {
            background: var(--primary-blue-dark);
          }
          .btn-secondary {
            background: var(--neutral-100);
            color: var(--neutral-700);
            border: 1px solid var(--neutral-300);
          }
          .btn-secondary:hover:not(:disabled) {
            background: var(--neutral-200);
          }
          .btn-small {
            padding: 4px 8px;
            font-size: 11px;
          }
          .btn-danger {
            background: var(--danger-red);
            color: white;
          }
          .btn-danger:hover:not(:disabled) {
            background: var(--danger-red-dark);
          }
          .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
          }
          .message {
            padding: 12px;
            border-radius: 4px;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 13px;
          }
          .message.success {
            background: var(--success-green-light);
            color: var(--success-green-dark);
            border: 1px solid var(--success-green);
          }
          .message.error {
            background: var(--danger-red-light);
            color: var(--danger-red-dark);
            border: 1px solid var(--danger-red);
          }
          .test-section, .headers-section, .auth-section {
            background: var(--neutral-50);
            border: 1px solid var(--neutral-200);
            border-radius: 6px;
            padding: 16px;
            margin-top: 20px;
          }
          .section-title {
            margin: 0 0 12px 0;
            font-size: 14px;
            font-weight: 600;
            color: var(--neutral-800);
          }
          .header-item {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 8px;
            padding: 8px;
            background: white;
            border: 1px solid var(--neutral-200);
            border-radius: 4px;
          }
          .header-key, .header-value {
            flex: 1;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            color: var(--neutral-700);
          }
          .add-header {
            display: flex;
            gap: 8px;
            align-items: end;
          }
          .add-header .form-input {
            flex: 1;
          }
          .help-section {
            background: var(--primary-blue-light);
            border: 1px solid var(--primary-blue);
            border-radius: 6px;
            padding: 12px;
            margin-bottom: 20px;
          }
          .help-section h4 {
            margin: 0 0 8px 0;
            font-size: 13px;
            font-weight: 600;
            color: var(--primary-blue-dark);
          }
          .help-section p {
            margin: 0 0 8px 0;
            font-size: 12px;
            color: var(--primary-blue-dark);
            line-height: 1.4;
          }
        `}
      </style>

      {message && (
        <div className={`message ${message.type}`}>
          {message.type === 'success' ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
          {message.text}
        </div>
      )}

      <div className="help-section">
        <h4>Generic Webhook Configuration</h4>
        <p>
          Configure a custom webhook endpoint to receive notifications. This allows integration with any service that accepts HTTP requests.
        </p>
        <p>
          <strong>Available template variables:</strong> <code>{'{{message}}'}</code>, <code>{'{{timestamp}}'}</code>, <code>{'{{subject}}'}</code>
        </p>
      </div>

      <div className="form-group">
        <label className="form-label">
          Webhook URL *
        </label>
        <input
          type="url"
          className="form-input"
          value={settings.url}
          onChange={(e) => setSettings({ ...settings, url: e.target.value })}
          placeholder="https://api.example.com/webhook"
          required
        />
        <div className="form-help">
          The endpoint URL where notifications will be sent
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label className="form-label">HTTP Method</label>
          <select
            className="form-select"
            value={settings.method}
            onChange={(e) => setSettings({ ...settings, method: e.target.value as 'POST' | 'PUT' | 'PATCH' })}
          >
            <option value="POST">POST</option>
            <option value="PUT">PUT</option>
            <option value="PATCH">PATCH</option>
          </select>
        </div>

        <div className="form-group">
          <label className="form-label">Content Type</label>
          <select
            className="form-select"
            value={settings.content_type}
            onChange={(e) => setSettings({ ...settings, content_type: e.target.value })}
          >
            <option value="application/json">application/json</option>
            <option value="application/x-www-form-urlencoded">application/x-www-form-urlencoded</option>
            <option value="text/plain">text/plain</option>
          </select>
        </div>
      </div>

      <div className="headers-section">
        <h4 className="section-title">Custom Headers</h4>
        
        {Object.entries(settings.headers || {}).map(([key, value]) => (
          <div key={key} className="header-item">
            <div className="header-key">{key}:</div>
            <div className="header-value">{value}</div>
            <button
              className="btn btn-danger btn-small"
              onClick={() => removeHeader(key)}
            >
              <Trash2 size={12} />
            </button>
          </div>
        ))}

        <div className="add-header">
          <div className="form-group" style={{ margin: 0, flex: 1 }}>
            <input
              type="text"
              className="form-input"
              placeholder="Header name"
              value={newHeaderKey}
              onChange={(e) => setNewHeaderKey(e.target.value)}
            />
          </div>
          <div className="form-group" style={{ margin: 0, flex: 1 }}>
            <input
              type="text"
              className="form-input"
              placeholder="Header value"
              value={newHeaderValue}
              onChange={(e) => setNewHeaderValue(e.target.value)}
            />
          </div>
          <button
            className="btn btn-secondary btn-small"
            onClick={addHeader}
            disabled={!newHeaderKey || !newHeaderValue}
          >
            <Plus size={12} />
            Add
          </button>
        </div>
      </div>

      <div className="auth-section">
        <h4 className="section-title">Authentication</h4>
        
        <div className="form-group">
          <label className="form-label">Authentication Type</label>
          <select
            className="form-select"
            value={settings.auth_type}
            onChange={(e) => setSettings({ ...settings, auth_type: e.target.value as any })}
          >
            <option value="none">None</option>
            <option value="basic">Basic Auth</option>
            <option value="bearer">Bearer Token</option>
            <option value="api_key">API Key</option>
          </select>
        </div>

        {settings.auth_type === 'basic' && (
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Username</label>
              <input
                type="text"
                className="form-input"
                value={settings.auth_config?.username || ''}
                onChange={(e) => updateAuthConfig('username', e.target.value)}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Password</label>
              <input
                type="password"
                className="form-input"
                value={settings.auth_config?.password || ''}
                onChange={(e) => updateAuthConfig('password', e.target.value)}
              />
            </div>
          </div>
        )}

        {settings.auth_type === 'bearer' && (
          <div className="form-group">
            <label className="form-label">Bearer Token</label>
            <input
              type="password"
              className="form-input"
              value={settings.auth_config?.token || ''}
              onChange={(e) => updateAuthConfig('token', e.target.value)}
              placeholder="your-bearer-token"
            />
          </div>
        )}

        {settings.auth_type === 'api_key' && (
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">API Key Header</label>
              <input
                type="text"
                className="form-input"
                value={settings.auth_config?.api_key_header || ''}
                onChange={(e) => updateAuthConfig('api_key_header', e.target.value)}
                placeholder="X-API-Key"
              />
            </div>
            <div className="form-group">
              <label className="form-label">API Key</label>
              <input
                type="password"
                className="form-input"
                value={settings.auth_config?.api_key || ''}
                onChange={(e) => updateAuthConfig('api_key', e.target.value)}
                placeholder="your-api-key"
              />
            </div>
          </div>
        )}
      </div>

      <div className="form-group">
        <label className="form-label">
          Payload Template
        </label>
        <textarea
          className="form-input form-textarea"
          value={settings.payload_template || ''}
          onChange={(e) => setSettings({ ...settings, payload_template: e.target.value })}
          placeholder='{"message": "{{message}}", "timestamp": "{{timestamp}}"}'
        />
        <div className="form-help">
          JSON template for the request body. Use <code>{'{{message}}'}</code>, <code>{'{{timestamp}}'}</code>, <code>{'{{subject}}'}</code> as placeholders.
        </div>
      </div>

      <div className="test-section">
        <h4 className="section-title">Test Configuration</h4>
        <div className="form-group">
          <label className="form-label">Test Message</label>
          <textarea
            className="form-input form-textarea"
            value={testMessage}
            onChange={(e) => setTestMessage(e.target.value)}
            placeholder="Enter a test message..."
          />
        </div>
        <button
          className="btn btn-secondary"
          onClick={handleTest}
          disabled={isTesting || !settings.url}
        >
          <Send size={14} />
          {isTesting ? 'Sending...' : 'Send Test Request'}
        </button>
      </div>

      <div className="button-group">
        <button
          className="btn btn-primary"
          onClick={handleSave}
          disabled={isSaving || !settings.url}
        >
          <Globe size={14} />
          {isSaving ? 'Saving...' : 'Save Webhook Settings'}
        </button>
      </div>
    </div>
  );
};

export default WebhookSettings;