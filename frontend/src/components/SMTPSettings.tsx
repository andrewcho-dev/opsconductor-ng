import React, { useState, useEffect } from 'react';
import { smtpApi } from '../services/api';
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
      const response = await smtpApi.getSMTPSettings();
      setCurrentSettings(response);
      
      // Populate form with current settings (password will be masked)
      if (response.data) {
        setSettings({
          host: response.data.host || '',
          port: response.data.port || 587,
          username: response.data.username || '',
          password: '', // Don't populate password field
          use_tls: response.data.use_tls !== false,
          from_email: response.data.from_email || '',
          from_name: response.data.from_name || 'OpsConductor'
        });
      } else {
        // No SMTP configuration found, use defaults
        setSettings({
          host: '',
          port: 587,
          username: '',
          password: '',
          use_tls: true,
          from_email: '',
          from_name: 'OpsConductor'
        });
      }
      
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
      
      const response = await smtpApi.updateSMTPSettings(settings);
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
      const response = await smtpApi.testSMTPSettings(testRequest);
      
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
    <div className="space-y-6">
      <style>
        {`
          .smtp-section {
            background: white;
            border: 1px solid var(--neutral-200);
            border-radius: 6px;
            overflow: hidden;
          }
          .smtp-header {
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
          .smtp-content {
            padding: 16px;
          }
          .form-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-bottom: 16px;
          }
          @media (max-width: 768px) {
            .form-grid {
              grid-template-columns: 1fr;
            }
          }
          .form-group {
            margin-bottom: 12px;
          }
          .form-label {
            display: block;
            font-size: 12px;
            font-weight: 500;
            color: var(--neutral-700);
            margin-bottom: 4px;
          }
          .form-input {
            width: 100%;
            padding: 8px 10px;
            border: 1px solid var(--neutral-300);
            border-radius: 4px;
            font-size: 12px;
            transition: border-color 0.2s, box-shadow 0.2s;
          }
          .form-input:focus {
            outline: none;
            border-color: var(--primary-blue);
            box-shadow: 0 0 0 2px var(--primary-blue-light);
          }
          .form-checkbox {
            display: flex;
            align-items: center;
            gap: 8px;
            margin: 12px 0;
          }
          .checkbox-input {
            width: 16px;
            height: 16px;
          }
          .checkbox-label {
            font-size: 12px;
            color: var(--neutral-700);
          }
          .test-row {
            display: flex;
            gap: 8px;
            align-items: stretch;
          }
          .test-input {
            flex: 1;
          }
          .test-button {
            padding: 8px 12px;
            background: var(--neutral-100);
            border: 1px solid var(--neutral-300);
            border-radius: 4px;
            font-size: 12px;
            cursor: pointer;
            transition: background-color 0.2s;
          }
          .test-button:hover:not(:disabled) {
            background: var(--neutral-200);
          }
          .test-button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
          }
          .save-button {
            background: var(--primary-blue);
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            transition: background-color 0.2s;
            display: flex;
            align-items: center;
            gap: 8px;
          }
          .save-button:hover:not(:disabled) {
            background: var(--primary-blue-hover);
          }
          .save-button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
          }
          .status-message {
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 12px;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
          }
          .status-success {
            background: var(--success-green-light);
            color: var(--success-green-dark);
            border: 1px solid var(--success-green);
          }
          .status-error {
            background: var(--danger-red-light);
            color: var(--danger-red);
            border: 1px solid var(--danger-red);
          }
          .status-configured {
            background: var(--success-green-light);
            color: var(--success-green-dark);
            font-size: 11px;
            padding: 4px 8px;
            border-radius: 3px;
            display: inline-flex;
            align-items: center;
            gap: 4px;
            margin-top: 8px;
          }
          .test-result {
            margin-top: 8px;
            padding: 8px;
            border-radius: 4px;
            font-size: 11px;
            display: flex;
            align-items: center;
            gap: 6px;
          }
          .test-result.success {
            background: var(--success-green-light);
            color: var(--success-green-dark);
          }
          .test-result.error {
            background: var(--danger-red-light);
            color: var(--danger-red);
          }
          .help-section {
            margin-top: 16px;
            padding: 12px;
            background: var(--primary-blue-light);
            border-radius: 4px;
            font-size: 11px;
            color: var(--primary-blue-dark);
          }
          .help-examples {
            margin-top: 8px;
            display: grid;
            gap: 4px;
          }
          .spinner {
            width: 14px;
            height: 14px;
            border: 2px solid transparent;
            border-top: 2px solid currentColor;
            border-radius: 50%;
            animation: spin 1s linear infinite;
          }
          @keyframes spin {
            to { transform: rotate(360deg); }
          }
        `}
      </style>

      {error && (
        <div className="status-message status-error">
          <XCircle size={14} />
          {error}
        </div>
      )}

      {success && (
        <div className="status-message status-success">
          <CheckCircle size={14} />
          {success}
        </div>
      )}

      <div className="smtp-section">
        <div className="smtp-header">
          SMTP Configuration
        </div>
        <div className="smtp-content">
          <p style={{ fontSize: '11px', color: 'var(--neutral-500)', marginBottom: '12px' }}>
            Configure SMTP settings for system-wide emails
          </p>
          
          {currentSettings?.data?.is_configured && (
            <div className="status-configured">
              <CheckCircle size={12} />
              SMTP configured and active
            </div>
          )}

          <div className="form-grid">
            <div className="form-group">
              <label className="form-label">SMTP Host *</label>
              <input
                type="text"
                value={settings.host || ''}
                onChange={(e) => handleInputChange('host', e.target.value)}
                className="form-input"
                placeholder="smtp.gmail.com"
              />
            </div>
            <div className="form-group">
              <label className="form-label">SMTP Port *</label>
              <input
                type="number"
                value={settings.port}
                onChange={(e) => handleInputChange('port', parseInt(e.target.value))}
                className="form-input"
                placeholder="587"
                min="1"
                max="65535"
              />
            </div>
          </div>

          <div className="form-checkbox">
            <input
              id="use_tls"
              type="checkbox"
              checked={settings.use_tls}
              onChange={(e) => handleInputChange('use_tls', e.target.checked)}
              className="checkbox-input"
            />
            <label htmlFor="use_tls" className="checkbox-label">
              Use TLS encryption (recommended)
            </label>
          </div>

          <div className="form-grid">
            <div className="form-group">
              <label className="form-label">Username</label>
              <input
                type="text"
                value={settings.username || ''}
                onChange={(e) => handleInputChange('username', e.target.value)}
                className="form-input"
                placeholder="your-email@gmail.com"
              />
            </div>
            <div className="form-group">
              <label className="form-label">Password</label>
              <input
                type="password"
                value={settings.password || ''}
                onChange={(e) => handleInputChange('password', e.target.value)}
                className="form-input"
                placeholder={currentSettings?.password ? "••••••••" : "Enter password"}
              />
              {currentSettings?.password && (
                <div style={{ fontSize: '10px', color: 'var(--neutral-500)', marginTop: '4px' }}>
                  Leave blank to keep current password
                </div>
              )}
            </div>
          </div>

          <div className="form-grid">
            <div className="form-group">
              <label className="form-label">From Email Address *</label>
              <input
                type="email"
                value={settings.from_email || ''}
                onChange={(e) => handleInputChange('from_email', e.target.value)}
                className="form-input"
                placeholder="noreply@yourcompany.com"
              />
            </div>
            <div className="form-group">
              <label className="form-label">From Name</label>
              <input
                type="text"
                value={settings.from_name || ''}
                onChange={(e) => handleInputChange('from_name', e.target.value)}
                className="form-input"
                placeholder="OpsConductor"
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Test Email Configuration</label>
            <div className="test-row">
              <input
                type="email"
                value={testEmail}
                onChange={(e) => setTestEmail(e.target.value)}
                className="form-input test-input"
                placeholder="test@example.com"
              />
              <button
                type="button"
                onClick={handleTest}
                disabled={testing || !testEmail}
                className="test-button"
              >
                {testing ? (
                  <>
                    <div className="spinner"></div>
                    Testing
                  </>
                ) : (
                  'Send Test'
                )}
              </button>
            </div>

            {testResult && (
              <div className={`test-result ${testSuccess ? 'success' : 'error'}`}>
                {testSuccess ? <CheckCircle size={12} /> : <XCircle size={12} />}
                {testResult}
              </div>
            )}
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '16px' }}>
            <button
              onClick={handleSave}
              disabled={saving}
              className="save-button"
            >
              {saving ? (
                <>
                  <div className="spinner"></div>
                  Saving
                </>
              ) : (
                'Save Settings'
              )}
            </button>
          </div>

          <div className="help-section">
            <strong>Common SMTP Settings:</strong>
            <div className="help-examples">
              <div><strong>Gmail:</strong> smtp.gmail.com:587 (TLS) - Use app password</div>
              <div><strong>Outlook:</strong> smtp-mail.outlook.com:587 (TLS)</div>
              <div><strong>Yahoo:</strong> smtp.mail.yahoo.com:587 (TLS)</div>
              <div><strong>SendGrid:</strong> smtp.sendgrid.net:587 (TLS)</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SMTPSettingsComponent;