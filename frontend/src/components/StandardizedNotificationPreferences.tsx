import React, { useState, useEffect } from 'react';
import { notificationApi } from '../services/api';
import { NotificationPreferences, NotificationPreferencesResponse } from '../types';
import { useAuth } from '../contexts/AuthContext';
import { 
  Mail, 
  Webhook, 
  MessageSquare, 
  Users, 
  Clock, 
  CheckCircle, 
  XCircle, 
  AlertCircle,
  Save,
  TestTube
} from 'lucide-react';

interface NotificationPreferencesProps {
  userId?: number;
  onSave?: (preferences: NotificationPreferencesResponse) => void;
}

const StandardizedNotificationPreferences: React.FC<NotificationPreferencesProps> = ({ 
  userId, 
  onSave 
}) => {
  const { user } = useAuth();
  const targetUserId = userId || user?.id;
  
  const [preferences, setPreferences] = useState<NotificationPreferences>({
    email_enabled: true,
    email_address: '',
    webhook_enabled: false,
    webhook_url: '',
    slack_enabled: false,
    slack_webhook_url: '',
    slack_channel: '',
    teams_enabled: false,
    teams_webhook_url: '',
    notify_on_success: true,
    notify_on_failure: true,
    notify_on_start: false,
    quiet_hours_enabled: false,
    quiet_hours_start: '',
    quiet_hours_end: '',
    quiet_hours_timezone: 'America/Los_Angeles'
  });

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const timezones = [
    'America/Los_Angeles',
    'America/Denver', 
    'America/Chicago',
    'America/New_York',
    'Europe/London',
    'Europe/Paris',
    'Asia/Tokyo',
    'Asia/Shanghai',
    'Australia/Sydney'
  ];

  useEffect(() => {
    fetchPreferences();
  }, [targetUserId]);

  const fetchPreferences = async () => {
    if (!targetUserId) return;
    
    try {
      setLoading(true);
      const response = await notificationApi.getUserPreferences(targetUserId);
      setPreferences(response);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load notification preferences');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!targetUserId) return;
    
    try {
      setSaving(true);
      setError(null);
      setSuccess(null);
      
      const response = await notificationApi.updateUserPreferences(targetUserId, preferences);
      setSuccess('Notification preferences saved successfully');
      
      if (onSave) {
        onSave(response);
      }
      
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err.message || 'Failed to save notification preferences');
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    // Test functionality not yet implemented
    setError('Test notification functionality is not yet available');
    setTimeout(() => setError(null), 3000);
  };

  const updatePreference = (key: keyof NotificationPreferences, value: any) => {
    setPreferences(prev => ({ ...prev, [key]: value }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="text-sm text-gray-500">Loading notification preferences...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <style>
        {`
          .pref-section {
            background: white;
            border: 1px solid var(--neutral-200);
            border-radius: 6px;
            overflow: hidden;
          }
          .pref-header {
            background: var(--neutral-50);
            padding: 12px 16px;
            border-bottom: 1px solid var(--neutral-200);
            font-weight: 600;
            font-size: 14px;
            color: var(--neutral-700);
            display: flex;
            align-items: center;
            gap: 8px;
          }
          .pref-content {
            padding: 16px;
          }
          .pref-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid var(--neutral-100);
          }
          .pref-row:last-child {
            border-bottom: none;
          }
          .pref-label {
            font-size: 13px;
            font-weight: 500;
            color: var(--neutral-700);
          }
          .pref-description {
            font-size: 11px;
            color: var(--neutral-500);
            margin-top: 2px;
          }
          .pref-control {
            display: flex;
            align-items: center;
            gap: 8px;
          }
          .toggle-switch {
            position: relative;
            width: 44px;
            height: 24px;
            background: var(--neutral-300);
            border-radius: 12px;
            cursor: pointer;
            transition: background 0.2s;
          }
          .toggle-switch.active {
            background: var(--primary-blue);
          }
          .toggle-switch::after {
            content: '';
            position: absolute;
            top: 2px;
            left: 2px;
            width: 20px;
            height: 20px;
            background: white;
            border-radius: 50%;
            transition: transform 0.2s;
          }
          .toggle-switch.active::after {
            transform: translateX(20px);
          }
          .form-input {
            padding: 6px 10px;
            border: 1px solid var(--neutral-300);
            border-radius: 4px;
            font-size: 12px;
            width: 200px;
          }
          .form-input:focus {
            outline: none;
            border-color: var(--primary-blue);
            box-shadow: 0 0 0 2px var(--primary-blue-light);
          }
          .form-select {
            padding: 6px 10px;
            border: 1px solid var(--neutral-300);
            border-radius: 4px;
            font-size: 12px;
            background: white;
            cursor: pointer;
          }
          .form-select:focus {
            outline: none;
            border-color: var(--primary-blue);
            box-shadow: 0 0 0 2px var(--primary-blue-light);
          }
          .btn-primary {
            background: var(--primary-blue);
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: all 0.15s;
          }
          .btn-primary:hover {
            background: var(--primary-blue-hover);
          }
          .btn-primary:disabled {
            opacity: 0.5;
            cursor: not-allowed;
          }
          .btn-secondary {
            background: var(--neutral-100);
            color: var(--neutral-700);
            border: 1px solid var(--neutral-300);
            padding: 8px 16px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: all 0.15s;
          }
          .btn-secondary:hover {
            background: var(--neutral-200);
          }
          .btn-secondary:disabled {
            opacity: 0.5;
            cursor: not-allowed;
          }
          .alert {
            padding: 12px;
            border-radius: 4px;
            font-size: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 16px;
          }
          .alert-success {
            background: var(--success-green-light);
            color: var(--success-green);
            border: 1px solid var(--success-green);
          }
          .alert-error {
            background: var(--danger-red-light);
            color: var(--danger-red);
            border: 1px solid var(--danger-red);
          }
          .actions-bar {
            display: flex;
            justify-content: flex-end;
            gap: 8px;
            padding: 16px;
            background: var(--neutral-50);
            border-top: 1px solid var(--neutral-200);
          }
        `}
      </style>

      {/* Status Messages */}
      {success && (
        <div className="alert alert-success">
          <CheckCircle size={16} />
          {success}
        </div>
      )}
      
      {error && (
        <div className="alert alert-error">
          <XCircle size={16} />
          {error}
        </div>
      )}

      {/* Email Notifications */}
      <div className="pref-section">
        <div className="pref-header">
          <Mail size={16} />
          Email Notifications
        </div>
        <div className="pref-content">
          <div className="pref-row">
            <div>
              <div className="pref-label">Enable Email Notifications</div>
              <div className="pref-description">Receive notifications via email</div>
            </div>
            <div className="pref-control">
              <div 
                className={`toggle-switch ${preferences.email_enabled ? 'active' : ''}`}
                onClick={() => updatePreference('email_enabled', !preferences.email_enabled)}
              />
            </div>
          </div>
          
          {preferences.email_enabled && (
            <div className="pref-row">
              <div>
                <div className="pref-label">Email Address</div>
                <div className="pref-description">Where to send email notifications</div>
              </div>
              <div className="pref-control">
                <input
                  type="email"
                  className="form-input"
                  value={preferences.email_address}
                  onChange={(e) => updatePreference('email_address', e.target.value)}
                  placeholder="your@email.com"
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Webhook Notifications */}
      <div className="pref-section">
        <div className="pref-header">
          <Webhook size={16} />
          Webhook Notifications
        </div>
        <div className="pref-content">
          <div className="pref-row">
            <div>
              <div className="pref-label">Enable Webhook Notifications</div>
              <div className="pref-description">Send notifications to a webhook URL</div>
            </div>
            <div className="pref-control">
              <div 
                className={`toggle-switch ${preferences.webhook_enabled ? 'active' : ''}`}
                onClick={() => updatePreference('webhook_enabled', !preferences.webhook_enabled)}
              />
            </div>
          </div>
          
          {preferences.webhook_enabled && (
            <div className="pref-row">
              <div>
                <div className="pref-label">Webhook URL</div>
                <div className="pref-description">HTTP endpoint to receive notifications</div>
              </div>
              <div className="pref-control">
                <input
                  type="url"
                  className="form-input"
                  value={preferences.webhook_url}
                  onChange={(e) => updatePreference('webhook_url', e.target.value)}
                  placeholder="https://your-webhook.com/notify"
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Slack Notifications */}
      <div className="pref-section">
        <div className="pref-header">
          <MessageSquare size={16} />
          Slack Notifications
        </div>
        <div className="pref-content">
          <div className="pref-row">
            <div>
              <div className="pref-label">Enable Slack Notifications</div>
              <div className="pref-description">Send notifications to Slack</div>
            </div>
            <div className="pref-control">
              <div 
                className={`toggle-switch ${preferences.slack_enabled ? 'active' : ''}`}
                onClick={() => updatePreference('slack_enabled', !preferences.slack_enabled)}
              />
            </div>
          </div>
          
          {preferences.slack_enabled && (
            <>
              <div className="pref-row">
                <div>
                  <div className="pref-label">Slack Webhook URL</div>
                  <div className="pref-description">Slack incoming webhook URL</div>
                </div>
                <div className="pref-control">
                  <input
                    type="url"
                    className="form-input"
                    value={preferences.slack_webhook_url}
                    onChange={(e) => updatePreference('slack_webhook_url', e.target.value)}
                    placeholder="https://hooks.slack.com/..."
                  />
                </div>
              </div>
              
              <div className="pref-row">
                <div>
                  <div className="pref-label">Slack Channel</div>
                  <div className="pref-description">Channel to post notifications (optional)</div>
                </div>
                <div className="pref-control">
                  <input
                    type="text"
                    className="form-input"
                    value={preferences.slack_channel}
                    onChange={(e) => updatePreference('slack_channel', e.target.value)}
                    placeholder="#notifications"
                  />
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Teams Notifications */}
      <div className="pref-section">
        <div className="pref-header">
          <Users size={16} />
          Microsoft Teams Notifications
        </div>
        <div className="pref-content">
          <div className="pref-row">
            <div>
              <div className="pref-label">Enable Teams Notifications</div>
              <div className="pref-description">Send notifications to Microsoft Teams</div>
            </div>
            <div className="pref-control">
              <div 
                className={`toggle-switch ${preferences.teams_enabled ? 'active' : ''}`}
                onClick={() => updatePreference('teams_enabled', !preferences.teams_enabled)}
              />
            </div>
          </div>
          
          {preferences.teams_enabled && (
            <div className="pref-row">
              <div>
                <div className="pref-label">Teams Webhook URL</div>
                <div className="pref-description">Teams incoming webhook URL</div>
              </div>
              <div className="pref-control">
                <input
                  type="url"
                  className="form-input"
                  value={preferences.teams_webhook_url}
                  onChange={(e) => updatePreference('teams_webhook_url', e.target.value)}
                  placeholder="https://outlook.office.com/webhook/..."
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Notification Events */}
      <div className="pref-section">
        <div className="pref-header">
          <AlertCircle size={16} />
          Notification Events
        </div>
        <div className="pref-content">
          <div className="pref-row">
            <div>
              <div className="pref-label">Job Success</div>
              <div className="pref-description">Notify when jobs complete successfully</div>
            </div>
            <div className="pref-control">
              <div 
                className={`toggle-switch ${preferences.notify_on_success ? 'active' : ''}`}
                onClick={() => updatePreference('notify_on_success', !preferences.notify_on_success)}
              />
            </div>
          </div>
          
          <div className="pref-row">
            <div>
              <div className="pref-label">Job Failure</div>
              <div className="pref-description">Notify when jobs fail or error</div>
            </div>
            <div className="pref-control">
              <div 
                className={`toggle-switch ${preferences.notify_on_failure ? 'active' : ''}`}
                onClick={() => updatePreference('notify_on_failure', !preferences.notify_on_failure)}
              />
            </div>
          </div>
          
          <div className="pref-row">
            <div>
              <div className="pref-label">Job Start</div>
              <div className="pref-description">Notify when jobs begin execution</div>
            </div>
            <div className="pref-control">
              <div 
                className={`toggle-switch ${preferences.notify_on_start ? 'active' : ''}`}
                onClick={() => updatePreference('notify_on_start', !preferences.notify_on_start)}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Quiet Hours */}
      <div className="pref-section">
        <div className="pref-header">
          <Clock size={16} />
          Quiet Hours
        </div>
        <div className="pref-content">
          <div className="pref-row">
            <div>
              <div className="pref-label">Enable Quiet Hours</div>
              <div className="pref-description">Suppress notifications during specified hours</div>
            </div>
            <div className="pref-control">
              <div 
                className={`toggle-switch ${preferences.quiet_hours_enabled ? 'active' : ''}`}
                onClick={() => updatePreference('quiet_hours_enabled', !preferences.quiet_hours_enabled)}
              />
            </div>
          </div>
          
          {preferences.quiet_hours_enabled && (
            <>
              <div className="pref-row">
                <div>
                  <div className="pref-label">Start Time</div>
                  <div className="pref-description">When quiet hours begin</div>
                </div>
                <div className="pref-control">
                  <input
                    type="time"
                    className="form-input"
                    value={preferences.quiet_hours_start}
                    onChange={(e) => updatePreference('quiet_hours_start', e.target.value)}
                  />
                </div>
              </div>
              
              <div className="pref-row">
                <div>
                  <div className="pref-label">End Time</div>
                  <div className="pref-description">When quiet hours end</div>
                </div>
                <div className="pref-control">
                  <input
                    type="time"
                    className="form-input"
                    value={preferences.quiet_hours_end}
                    onChange={(e) => updatePreference('quiet_hours_end', e.target.value)}
                  />
                </div>
              </div>
              
              <div className="pref-row">
                <div>
                  <div className="pref-label">Timezone</div>
                  <div className="pref-description">Timezone for quiet hours</div>
                </div>
                <div className="pref-control">
                  <select
                    className="form-select"
                    value={preferences.quiet_hours_timezone}
                    onChange={(e) => updatePreference('quiet_hours_timezone', e.target.value)}
                  >
                    {timezones.map(tz => (
                      <option key={tz} value={tz}>{tz}</option>
                    ))}
                  </select>
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="pref-section">
        <div className="actions-bar">
          <button
            className="btn-secondary"
            onClick={handleTest}
            disabled={testing || saving}
          >
            <TestTube size={14} />
            {testing ? 'Testing...' : 'Test Notification'}
          </button>
          <button
            className="btn-primary"
            onClick={handleSave}
            disabled={saving || testing}
          >
            <Save size={14} />
            {saving ? 'Saving...' : 'Save Preferences'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default StandardizedNotificationPreferences;