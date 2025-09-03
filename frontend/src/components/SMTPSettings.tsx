import React, { useState, useEffect } from 'react';
import { notificationApi } from '../services/api';
import { SMTPSettings, SMTPSettingsResponse, SMTPTestRequest } from '../types';
import { useAuth } from '../contexts/AuthContext';
import { CheckCircle, XCircle } from 'lucide-react';

const SMTPSettingsComponent: React.FC = () => {
  const { user } = useAuth();
  const [settings, setSettings] = useState<SMTPSettings>({
    host: '',
    port: 587,
    username: '',
    password: '',
    use_tls: true,
    from_email: '',
    from_name: 'OpsConductor'
  });

  const [currentSettings, setCurrentSettings] = useState<SMTPSettingsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [testEmail, setTestEmail] = useState('');
  const [testResult, setTestResult] = useState<string | null>(null);
  const [testSuccess, setTestSuccess] = useState<boolean | null>(null);

  useEffect(() => {
    if (user?.role === 'admin') {
      loadSettings();
    }
  }, [user?.role]);

  // Only allow admin users
  if (user?.role !== 'admin') {
    return (
      <div className="bg-yellow-50 border border-yellow-200 text-yellow-700 px-4 py-3 rounded">
        Access denied. Only administrators can configure SMTP settings.
      </div>
    );
  }

  const loadSettings = async () => {
    try {
      setLoading(true);
      const response = await notificationApi.getSMTPSettings();
      setCurrentSettings(response);
      
      // Populate form with current settings (password will be masked)
      setSettings({
        host: response.host,
        port: response.port,
        username: response.username,
        password: '', // Don't populate password field
        use_tls: response.use_tls,
        from_email: response.from_email,
        from_name: response.from_name
      });
      
      setError(null);
    } catch (err: any) {
      console.error('Failed to load SMTP settings:', err);
      setError('Failed to load SMTP settings');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);
      setSuccess(null);
      
      const response = await notificationApi.updateSMTPSettings(settings);
      setCurrentSettings(response);
      setSuccess('SMTP settings saved successfully!');
      
      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      console.error('Failed to save SMTP settings:', err);
      setError(err.response?.data?.detail || 'Failed to save SMTP settings');
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    if (!testEmail) {
      setError('Please enter a test email address');
      return;
    }

    try {
      setTesting(true);
      setError(null);
      setTestResult(null);
      
      const testRequest: SMTPTestRequest = { test_email: testEmail };
      const response = await notificationApi.testSMTPSettings(testRequest);
      
      if (response.success) {
        setTestResult(response.message);
        setTestSuccess(true);
      } else {
        setTestResult(response.message);
        setTestSuccess(false);
      }
    } catch (err: any) {
      console.error('SMTP test failed:', err);
      setTestResult(`Test failed: ${err.response?.data?.detail || err.message}`);
      setTestSuccess(false);
    } finally {
      setTesting(false);
    }
  };

  const handleInputChange = (field: keyof SMTPSettings, value: any) => {
    setSettings(prev => ({
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
          SMTP Configuration
        </h3>
        <p className="text-sm text-gray-600">
          Configure SMTP settings for email notifications. These settings apply system-wide.
        </p>
        {currentSettings?.is_configured && (
          <div className="mt-2 text-sm text-green-600">
            <CheckCircle size={16} className="inline mr-2" />SMTP is currently configured and active
          </div>
        )}
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
        {/* Server Settings */}
        <div className="border-b border-gray-200 pb-6">
          <h4 className="text-md font-medium text-gray-900 mb-4">Server Settings</h4>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="smtp_host" className="block text-sm font-medium text-gray-700">
                SMTP Host *
              </label>
              <input
                type="text"
                id="smtp_host"
                value={settings.host}
                onChange={(e) => handleInputChange('host', e.target.value)}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="smtp.gmail.com"
                required
              />
            </div>

            <div>
              <label htmlFor="smtp_port" className="block text-sm font-medium text-gray-700">
                SMTP Port *
              </label>
              <input
                type="number"
                id="smtp_port"
                value={settings.port}
                onChange={(e) => handleInputChange('port', parseInt(e.target.value))}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="587"
                min="1"
                max="65535"
                required
              />
            </div>
          </div>

          <div className="mt-4">
            <div className="flex items-center">
              <input
                id="use_tls"
                type="checkbox"
                checked={settings.use_tls}
                onChange={(e) => handleInputChange('use_tls', e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="use_tls" className="ml-2 block text-sm text-gray-900">
                Use TLS encryption (recommended)
              </label>
            </div>
          </div>
        </div>

        {/* Authentication */}
        <div className="border-b border-gray-200 pb-6">
          <h4 className="text-md font-medium text-gray-900 mb-4">Authentication</h4>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="smtp_username" className="block text-sm font-medium text-gray-700">
                Username
              </label>
              <input
                type="text"
                id="smtp_username"
                value={settings.username}
                onChange={(e) => handleInputChange('username', e.target.value)}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="your-email@gmail.com"
              />
            </div>

            <div>
              <label htmlFor="smtp_password" className="block text-sm font-medium text-gray-700">
                Password
              </label>
              <input
                type="password"
                id="smtp_password"
                value={settings.password}
                onChange={(e) => handleInputChange('password', e.target.value)}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder={currentSettings?.password ? "••••••••" : "Enter password"}
              />
              {currentSettings?.password && (
                <p className="mt-1 text-xs text-gray-500">
                  Leave blank to keep current password
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Sender Information */}
        <div className="border-b border-gray-200 pb-6">
          <h4 className="text-md font-medium text-gray-900 mb-4">Sender Information</h4>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="from_email" className="block text-sm font-medium text-gray-700">
                From Email Address *
              </label>
              <input
                type="email"
                id="from_email"
                value={settings.from_email}
                onChange={(e) => handleInputChange('from_email', e.target.value)}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="noreply@yourcompany.com"
                required
              />
            </div>

            <div>
              <label htmlFor="from_name" className="block text-sm font-medium text-gray-700">
                From Name
              </label>
              <input
                type="text"
                id="from_name"
                value={settings.from_name}
                onChange={(e) => handleInputChange('from_name', e.target.value)}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="OpsConductor"
              />
            </div>
          </div>
        </div>

        {/* Test Settings */}
        <div className="pb-6">
          <h4 className="text-md font-medium text-gray-900 mb-4">Test Configuration</h4>
          
          <div className="space-y-4">
            <div>
              <label htmlFor="test_email" className="block text-sm font-medium text-gray-700">
                Test Email Address
              </label>
              <div className="mt-1 flex rounded-md shadow-sm">
                <input
                  type="email"
                  id="test_email"
                  value={testEmail}
                  onChange={(e) => setTestEmail(e.target.value)}
                  className="flex-1 block w-full border-gray-300 rounded-l-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  placeholder="test@example.com"
                />
                <button
                  type="button"
                  onClick={handleTest}
                  disabled={testing || !testEmail}
                  className="inline-flex items-center px-3 py-2 border border-l-0 border-gray-300 rounded-r-md bg-gray-50 text-gray-500 text-sm hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {testing ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600 mr-2"></div>
                      Testing...
                    </>
                  ) : (
                    'Send Test'
                  )}
                </button>
              </div>
            </div>

            {testResult && (
              <div className={`p-3 rounded-md text-sm flex items-center gap-2 ${
                testSuccess 
                  ? 'bg-green-50 text-green-700 border border-green-200' 
                  : 'bg-red-50 text-red-700 border border-red-200'
              }`}>
                {testSuccess ? <CheckCircle size={16} /> : <XCircle size={16} />}
                {testResult}
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
            'Save SMTP Settings'
          )}
        </button>
      </div>

      {/* Help Text */}
      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-md">
        <h5 className="text-sm font-medium text-blue-900 mb-2">Common SMTP Settings:</h5>
        <div className="text-xs text-blue-700 space-y-1">
          <div><strong>Gmail:</strong> smtp.gmail.com:587 (TLS) - Use app password</div>
          <div><strong>Outlook:</strong> smtp-mail.outlook.com:587 (TLS)</div>
          <div><strong>Yahoo:</strong> smtp.mail.yahoo.com:587 (TLS)</div>
          <div><strong>SendGrid:</strong> smtp.sendgrid.net:587 (TLS)</div>
        </div>
      </div>
    </div>
  );
};

export default SMTPSettingsComponent;