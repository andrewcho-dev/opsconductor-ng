import React, { useState, useEffect } from 'react';
import { communicationApi } from '../services/api';
import { SlackSettings as SlackSettingsType, CommunicationTestRequest } from '../types';
import { MessageSquare, Send, AlertCircle, CheckCircle, ExternalLink } from 'lucide-react';

const SlackSettings: React.FC = () => {
  const [settings, setSettings] = useState<SlackSettingsType>({
    webhook_url: '',
    channel: '',
    username: 'OpsConductor',
    icon_emoji: ':robot_face:'
  });
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [testMessage, setTestMessage] = useState('This is a test message from OpsConductor!');

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    setIsLoading(true);
    try {
      const channel = await communicationApi.getChannelByType('slack');
      if (channel) {
        setSettings(channel.configuration as SlackSettingsType);
      }
    } catch (error) {
      console.error('Failed to load Slack settings:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    setMessage(null);
    try {
      await communicationApi.saveChannel({
        name: 'Slack Notifications',
        channel_type: 'slack',
        configuration: settings,
        is_active: true
      });
      setMessage({ type: 'success', text: 'Slack settings saved successfully!' });
    } catch (error: any) {
      setMessage({ type: 'error', text: error.message || 'Failed to save Slack settings' });
    } finally {
      setIsSaving(false);
    }
  };

  const handleTest = async () => {
    if (!settings.webhook_url) {
      setMessage({ type: 'error', text: 'Please configure webhook URL before testing' });
      return;
    }

    setIsTesting(true);
    setMessage(null);
    try {
      const testRequest: CommunicationTestRequest = {
        channel_type: 'slack',
        test_message: testMessage
      };
      const result = await communicationApi.testChannel('slack', testRequest);
      setMessage({ 
        type: result.success ? 'success' : 'error', 
        text: result.message 
      });
    } catch (error: any) {
      setMessage({ type: 'error', text: error.message || 'Failed to test Slack configuration' });
    } finally {
      setIsTesting(false);
    }
  };

  if (isLoading) {
    return <div style={{ padding: '20px', textAlign: 'center' }}>Loading Slack settings...</div>;
  }

  return (
    <div className="slack-settings">
      <style>
        {`
          .slack-settings {
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
          .form-input {
            width: 100%;
            padding: 8px 12px;
            border: 1px solid var(--neutral-300);
            border-radius: 4px;
            font-size: 13px;
            transition: border-color 0.15s;
          }
          .form-input:focus {
            outline: none;
            border-color: var(--primary-blue);
            box-shadow: 0 0 0 2px var(--primary-blue-light);
          }
          .form-textarea {
            min-height: 80px;
            resize: vertical;
          }
          .form-help {
            font-size: 11px;
            color: var(--neutral-500);
            margin-top: 4px;
            line-height: 1.4;
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
          .test-section {
            background: var(--neutral-50);
            border: 1px solid var(--neutral-200);
            border-radius: 6px;
            padding: 16px;
            margin-top: 20px;
          }
          .test-section h4 {
            margin: 0 0 12px 0;
            font-size: 14px;
            font-weight: 600;
            color: var(--neutral-800);
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
          .help-section a {
            color: var(--primary-blue-dark);
            text-decoration: underline;
          }
          .help-section a:hover {
            text-decoration: none;
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
        <h4>Setting up Slack Webhooks</h4>
        <p>
          1. Go to your Slack workspace and create a new app at{' '}
          <a href="https://api.slack.com/apps" target="_blank" rel="noopener noreferrer">
            api.slack.com/apps <ExternalLink size={12} style={{ display: 'inline' }} />
          </a>
        </p>
        <p>2. Enable "Incoming Webhooks" and create a new webhook URL</p>
        <p>3. Copy the webhook URL and paste it below</p>
      </div>

      <div className="form-group">
        <label className="form-label">
          Webhook URL *
        </label>
        <input
          type="url"
          className="form-input"
          value={settings.webhook_url}
          onChange={(e) => setSettings({ ...settings, webhook_url: e.target.value })}
          placeholder="https://hooks.slack.com/services/..."
          required
        />
        <div className="form-help">
          The incoming webhook URL from your Slack app configuration
        </div>
      </div>

      <div className="form-group">
        <label className="form-label">
          Channel
        </label>
        <input
          type="text"
          className="form-input"
          value={settings.channel || ''}
          onChange={(e) => setSettings({ ...settings, channel: e.target.value })}
          placeholder="#general"
        />
        <div className="form-help">
          Override the default channel (optional). Use #channel-name or @username
        </div>
      </div>

      <div className="form-group">
        <label className="form-label">
          Bot Username
        </label>
        <input
          type="text"
          className="form-input"
          value={settings.username || ''}
          onChange={(e) => setSettings({ ...settings, username: e.target.value })}
          placeholder="OpsConductor"
        />
        <div className="form-help">
          The name that will appear as the sender of messages
        </div>
      </div>

      <div className="form-group">
        <label className="form-label">
          Icon Emoji
        </label>
        <input
          type="text"
          className="form-input"
          value={settings.icon_emoji || ''}
          onChange={(e) => setSettings({ ...settings, icon_emoji: e.target.value })}
          placeholder=":robot_face:"
        />
        <div className="form-help">
          Emoji to use as the bot's avatar (e.g., :robot_face:, :gear:)
        </div>
      </div>

      <div className="test-section">
        <h4>Test Configuration</h4>
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
          disabled={isTesting || !settings.webhook_url}
        >
          <Send size={14} />
          {isTesting ? 'Sending...' : 'Send Test Message'}
        </button>
      </div>

      <div className="button-group">
        <button
          className="btn btn-primary"
          onClick={handleSave}
          disabled={isSaving || !settings.webhook_url}
        >
          <MessageSquare size={14} />
          {isSaving ? 'Saving...' : 'Save Slack Settings'}
        </button>
      </div>
    </div>
  );
};

export default SlackSettings;