import React, { useState, useEffect } from 'react';
import { notificationApi } from '../services/api';
import { NotificationPreferences, NotificationPreferencesResponse } from '../types';
import { useAuth } from '../contexts/AuthContext';

interface NotificationPreferencesProps {
  userId?: number;
  onSave?: (preferences: NotificationPreferencesResponse) => void;
}

const NotificationPreferencesComponent: React.FC<NotificationPreferencesProps> = ({ 
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
    if (targetUserId) {
      loadPreferences();
    }
  }, [targetUserId]);

  const loadPreferences = async () => {
    if (!targetUserId) return;
    
    try {
      setLoading(true);
      const response = await notificationApi.getUserPreferences(targetUserId);
      setPreferences(response);
      setError(null);
    } catch (err: any) {
      console.error('Failed to load notification preferences:', err);
      setError('Failed to load notification preferences');
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
      setSuccess('Notification preferences saved successfully!');
      
      if (onSave) {
        onSave(response);
      }
      
      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      console.error('Failed to save notification preferences:', err);
      setError(err.response?.data?.detail || 'Failed to save notification preferences');
    } finally {
      setSaving(false);
    }
  };

  const handleInputChange = (field: keyof NotificationPreferences, value: any) => {
    setPreferences(prev => ({
      ...prev,
      [field]: value
    }));
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <div className="mb-6">
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          Notification Preferences
        </h3>
        <p className="text-sm text-gray-600">
          Configure how and when you want to receive job notifications.
        </p>
      </div>

      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {success && (
        <div className="mb-4 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded">
          {success}
        </div>
      )}

      <div className="space-y-6">
        {/* Email Notifications */}
        <div className="border-b border-gray-200 pb-6">
          <h4 className="text-md font-medium text-gray-900 mb-4">Email Notifications</h4>
          
          <div className="space-y-4">
            <div className="flex items-center">
              <input
                id="email_enabled"
                type="checkbox"
                checked={preferences.email_enabled}
                onChange={(e) => handleInputChange('email_enabled', e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="email_enabled" className="ml-2 block text-sm text-gray-900">
                Enable email notifications
              </label>
            </div>

            {preferences.email_enabled && (
              <div>
                <label htmlFor="email_address" className="block text-sm font-medium text-gray-700">
                  Email Address (optional - uses account email if not specified)
                </label>
                <input
                  type="email"
                  id="email_address"
                  value={preferences.email_address || ''}
                  onChange={(e) => handleInputChange('email_address', e.target.value)}
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  placeholder="user@example.com"
                />
              </div>
            )}
          </div>
        </div>

        {/* Slack Notifications */}
        <div className="border-b border-gray-200 pb-6">
          <h4 className="text-md font-medium text-gray-900 mb-4">Slack Notifications</h4>
          
          <div className="space-y-4">
            <div className="flex items-center">
              <input
                id="slack_enabled"
                type="checkbox"
                checked={preferences.slack_enabled}
                onChange={(e) => handleInputChange('slack_enabled', e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="slack_enabled" className="ml-2 block text-sm text-gray-900">
                Enable Slack notifications
              </label>
            </div>

            {preferences.slack_enabled && (
              <>
                <div>
                  <label htmlFor="slack_webhook_url" className="block text-sm font-medium text-gray-700">
                    Slack Webhook URL *
                  </label>
                  <input
                    type="url"
                    id="slack_webhook_url"
                    value={preferences.slack_webhook_url || ''}
                    onChange={(e) => handleInputChange('slack_webhook_url', e.target.value)}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    placeholder="https://hooks.slack.com/services/..."
                    required
                  />
                </div>
                <div>
                  <label htmlFor="slack_channel" className="block text-sm font-medium text-gray-700">
                    Slack Channel (optional)
                  </label>
                  <input
                    type="text"
                    id="slack_channel"
                    value={preferences.slack_channel || ''}
                    onChange={(e) => handleInputChange('slack_channel', e.target.value)}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    placeholder="#notifications"
                  />
                </div>
              </>
            )}
          </div>
        </div>

        {/* Microsoft Teams Notifications */}
        <div className="border-b border-gray-200 pb-6">
          <h4 className="text-md font-medium text-gray-900 mb-4">Microsoft Teams Notifications</h4>
          
          <div className="space-y-4">
            <div className="flex items-center">
              <input
                id="teams_enabled"
                type="checkbox"
                checked={preferences.teams_enabled}
                onChange={(e) => handleInputChange('teams_enabled', e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="teams_enabled" className="ml-2 block text-sm text-gray-900">
                Enable Microsoft Teams notifications
              </label>
            </div>

            {preferences.teams_enabled && (
              <div>
                <label htmlFor="teams_webhook_url" className="block text-sm font-medium text-gray-700">
                  Teams Webhook URL *
                </label>
                <input
                  type="url"
                  id="teams_webhook_url"
                  value={preferences.teams_webhook_url || ''}
                  onChange={(e) => handleInputChange('teams_webhook_url', e.target.value)}
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  placeholder="https://outlook.office.com/webhook/..."
                  required
                />
              </div>
            )}
          </div>
        </div>

        {/* Generic Webhook Notifications */}
        <div className="border-b border-gray-200 pb-6">
          <h4 className="text-md font-medium text-gray-900 mb-4">Generic Webhook Notifications</h4>
          
          <div className="space-y-4">
            <div className="flex items-center">
              <input
                id="webhook_enabled"
                type="checkbox"
                checked={preferences.webhook_enabled}
                onChange={(e) => handleInputChange('webhook_enabled', e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="webhook_enabled" className="ml-2 block text-sm text-gray-900">
                Enable generic webhook notifications
              </label>
            </div>

            {preferences.webhook_enabled && (
              <div>
                <label htmlFor="webhook_url" className="block text-sm font-medium text-gray-700">
                  Webhook URL *
                </label>
                <input
                  type="url"
                  id="webhook_url"
                  value={preferences.webhook_url || ''}
                  onChange={(e) => handleInputChange('webhook_url', e.target.value)}
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  placeholder="https://your-webhook-endpoint.com/notifications"
                  required
                />
              </div>
            )}
          </div>
        </div>

        {/* Event Types */}
        <div className="border-b border-gray-200 pb-6">
          <h4 className="text-md font-medium text-gray-900 mb-4">Notification Events</h4>
          
          <div className="space-y-3">
            <div className="flex items-center">
              <input
                id="notify_on_success"
                type="checkbox"
                checked={preferences.notify_on_success}
                onChange={(e) => handleInputChange('notify_on_success', e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="notify_on_success" className="ml-2 block text-sm text-gray-900">
                Notify on job success
              </label>
            </div>

            <div className="flex items-center">
              <input
                id="notify_on_failure"
                type="checkbox"
                checked={preferences.notify_on_failure}
                onChange={(e) => handleInputChange('notify_on_failure', e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="notify_on_failure" className="ml-2 block text-sm text-gray-900">
                Notify on job failure
              </label>
            </div>

            <div className="flex items-center">
              <input
                id="notify_on_start"
                type="checkbox"
                checked={preferences.notify_on_start}
                onChange={(e) => handleInputChange('notify_on_start', e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="notify_on_start" className="ml-2 block text-sm text-gray-900">
                Notify on job start
              </label>
            </div>
          </div>
        </div>

        {/* Quiet Hours */}
        <div className="pb-6">
          <h4 className="text-md font-medium text-gray-900 mb-4">Quiet Hours</h4>
          
          <div className="space-y-4">
            <div className="flex items-center">
              <input
                id="quiet_hours_enabled"
                type="checkbox"
                checked={preferences.quiet_hours_enabled}
                onChange={(e) => handleInputChange('quiet_hours_enabled', e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="quiet_hours_enabled" className="ml-2 block text-sm text-gray-900">
                Enable quiet hours (only critical failures will be sent during this time)
              </label>
            </div>

            {preferences.quiet_hours_enabled && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label htmlFor="quiet_hours_start" className="block text-sm font-medium text-gray-700">
                    Start Time
                  </label>
                  <input
                    type="time"
                    id="quiet_hours_start"
                    value={preferences.quiet_hours_start || ''}
                    onChange={(e) => handleInputChange('quiet_hours_start', e.target.value)}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  />
                </div>

                <div>
                  <label htmlFor="quiet_hours_end" className="block text-sm font-medium text-gray-700">
                    End Time
                  </label>
                  <input
                    type="time"
                    id="quiet_hours_end"
                    value={preferences.quiet_hours_end || ''}
                    onChange={(e) => handleInputChange('quiet_hours_end', e.target.value)}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  />
                </div>

                <div>
                  <label htmlFor="quiet_hours_timezone" className="block text-sm font-medium text-gray-700">
                    Timezone
                  </label>
                  <select
                    id="quiet_hours_timezone"
                    value={preferences.quiet_hours_timezone}
                    onChange={(e) => handleInputChange('quiet_hours_timezone', e.target.value)}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  >
                    {timezones.map(tz => (
                      <option key={tz} value={tz}>{tz}</option>
                    ))}
                  </select>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end pt-6 border-t border-gray-200">
        <button
          onClick={handleSave}
          disabled={saving}
          className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {saving ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Saving...
            </>
          ) : (
            'Save Preferences'
          )}
        </button>
      </div>
    </div>
  );
};

export default NotificationPreferencesComponent;