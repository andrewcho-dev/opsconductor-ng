import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';

interface SMTPSettings {
  host: string;
  port: number;
  username: string;
  password: string;
  use_tls: boolean;
  from_email: string;
  from_name: string;
  is_configured: boolean;
}

interface SMTPTestResult {
  success: boolean;
  message: string;
}

const Settings: React.FC = () => {
  const { token } = useAuth();
  const [smtpSettings, setSmtpSettings] = useState<SMTPSettings>({
    host: '',
    port: 587,
    username: '',
    password: '',
    use_tls: true,
    from_email: '',
    from_name: 'OpsConductor',
    is_configured: false
  });
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [testEmail, setTestEmail] = useState('');
  const [testResult, setTestResult] = useState<SMTPTestResult | null>(null);
  const [showPassword, setShowPassword] = useState(false);

  const fetchSMTPSettings = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/notification/smtp/settings', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setSmtpSettings(data);
      setError(null);
    } catch (err) {
      console.error('Error fetching SMTP settings:', err);
      setError('Failed to fetch SMTP settings');
    } finally {
      setLoading(false);
    }
  };

  const saveSMTPSettings = async () => {
    try {
      setSaving(true);
      setError(null);
      setSuccess(null);

      const response = await fetch('/api/notification/smtp/settings', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          host: smtpSettings.host,
          port: smtpSettings.port,
          username: smtpSettings.username,
          password: smtpSettings.password,
          use_tls: smtpSettings.use_tls,
          from_email: smtpSettings.from_email,
          from_name: smtpSettings.from_name
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      setSuccess('SMTP settings saved successfully!');
      // Refresh settings to get updated data
      await fetchSMTPSettings();
    } catch (err) {
      console.error('Error saving SMTP settings:', err);
      setError('Failed to save SMTP settings');
    } finally {
      setSaving(false);
    }
  };

  const testSMTPSettings = async () => {
    if (!testEmail) {
      setError('Please enter a test email address');
      return;
    }

    try {
      setTesting(true);
      setTestResult(null);
      setError(null);

      const response = await fetch('/api/notification/smtp/test', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          test_email: testEmail
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setTestResult(result);
    } catch (err) {
      console.error('Error testing SMTP settings:', err);
      setTestResult({
        success: false,
        message: 'Failed to test SMTP settings'
      });
    } finally {
      setTesting(false);
    }
  };

  useEffect(() => {
    fetchSMTPSettings();
  }, [token]);

  const handleInputChange = (field: keyof SMTPSettings, value: any) => {
    setSmtpSettings(prev => ({
      ...prev,
      [field]: value
    }));
    // Clear success message when user starts editing
    if (success) setSuccess(null);
  };

  const clearMessages = () => {
    setError(null);
    setSuccess(null);
    setTestResult(null);
  };

  return (
    <div style={{ padding: '20px' }}>
      <h1>System Settings</h1>

      {/* Alert Messages */}
      {error && (
        <div className="alert alert-danger" style={{ marginBottom: '20px' }}>
          {error}
          <button 
            onClick={clearMessages}
            style={{ float: 'right', background: 'none', border: 'none', fontSize: '18px' }}
          >
            ×
          </button>
        </div>
      )}

      {success && (
        <div className="alert alert-success" style={{ marginBottom: '20px' }}>
          {success}
          <button 
            onClick={clearMessages}
            style={{ float: 'right', background: 'none', border: 'none', fontSize: '18px' }}
          >
            ×
          </button>
        </div>
      )}

      {testResult && (
        <div className={`alert ${testResult.success ? 'alert-success' : 'alert-danger'}`} style={{ marginBottom: '20px' }}>
          <strong>{testResult.success ? 'Test Successful!' : 'Test Failed!'}</strong>
          <br />
          {testResult.message}
          <button 
            onClick={clearMessages}
            style={{ float: 'right', background: 'none', border: 'none', fontSize: '18px' }}
          >
            ×
          </button>
        </div>
      )}

      {/* SMTP Configuration Card */}
      <div className="card">
        <div className="card-header">
          <h3>
            📧 SMTP Email Configuration
            {smtpSettings.is_configured && (
              <span className="badge badge-success" style={{ marginLeft: '10px', backgroundColor: '#28a745' }}>
                Configured
              </span>
            )}
          </h3>
        </div>
        <div className="card-body">
          {loading ? (
            <div style={{ textAlign: 'center', padding: '20px' }}>
              Loading...
            </div>
          ) : (
            <form onSubmit={(e) => { e.preventDefault(); saveSMTPSettings(); }}>
              <div className="row">
                {/* SMTP Host */}
                <div className="col-md-8">
                  <div className="form-group" style={{ marginBottom: '15px' }}>
                    <label htmlFor="smtp-host">
                      <strong>SMTP Host *</strong>
                    </label>
                    <input
                      id="smtp-host"
                      type="text"
                      className="form-control"
                      value={smtpSettings.host}
                      onChange={(e) => handleInputChange('host', e.target.value)}
                      placeholder="smtp.gmail.com"
                      required
                    />
                    <small className="form-text text-muted">
                      Your SMTP server hostname (e.g., smtp.gmail.com, smtp.office365.com)
                    </small>
                  </div>
                </div>

                {/* SMTP Port */}
                <div className="col-md-4">
                  <div className="form-group" style={{ marginBottom: '15px' }}>
                    <label htmlFor="smtp-port">
                      <strong>Port *</strong>
                    </label>
                    <input
                      id="smtp-port"
                      type="number"
                      className="form-control"
                      value={smtpSettings.port}
                      onChange={(e) => handleInputChange('port', parseInt(e.target.value) || 587)}
                      min="1"
                      max="65535"
                      required
                    />
                    <small className="form-text text-muted">
                      Usually 587 (TLS) or 465 (SSL)
                    </small>
                  </div>
                </div>
              </div>

              <div className="row">
                {/* Username */}
                <div className="col-md-6">
                  <div className="form-group" style={{ marginBottom: '15px' }}>
                    <label htmlFor="smtp-username">
                      <strong>Username</strong>
                    </label>
                    <input
                      id="smtp-username"
                      type="text"
                      className="form-control"
                      value={smtpSettings.username}
                      onChange={(e) => handleInputChange('username', e.target.value)}
                      placeholder="your-email@gmail.com"
                    />
                    <small className="form-text text-muted">
                      Leave empty if no authentication required
                    </small>
                  </div>
                </div>

                {/* Password */}
                <div className="col-md-6">
                  <div className="form-group" style={{ marginBottom: '15px' }}>
                    <label htmlFor="smtp-password">
                      <strong>Password</strong>
                    </label>
                    <div style={{ position: 'relative' }}>
                      <input
                        id="smtp-password"
                        type={showPassword ? "text" : "password"}
                        className="form-control"
                        value={smtpSettings.password}
                        onChange={(e) => handleInputChange('password', e.target.value)}
                        placeholder="Enter password or app password"
                        style={{ paddingRight: '40px' }}
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        style={{
                          position: 'absolute',
                          right: '10px',
                          top: '50%',
                          transform: 'translateY(-50%)',
                          background: 'none',
                          border: 'none',
                          cursor: 'pointer'
                        }}
                      >
                        {showPassword ? '👁️' : '👁️‍🗨️'}
                      </button>
                    </div>
                    <small className="form-text text-muted">
                      For Gmail, use an App Password instead of your regular password
                    </small>
                  </div>
                </div>
              </div>

              {/* TLS Setting */}
              <div className="form-group" style={{ marginBottom: '15px' }}>
                <div className="form-check">
                  <input
                    id="smtp-tls"
                    type="checkbox"
                    className="form-check-input"
                    checked={smtpSettings.use_tls}
                    onChange={(e) => handleInputChange('use_tls', e.target.checked)}
                  />
                  <label htmlFor="smtp-tls" className="form-check-label">
                    <strong>Use TLS Encryption</strong>
                  </label>
                </div>
                <small className="form-text text-muted">
                  Recommended for secure email transmission
                </small>
              </div>

              <div className="row">
                {/* From Email */}
                <div className="col-md-6">
                  <div className="form-group" style={{ marginBottom: '15px' }}>
                    <label htmlFor="smtp-from-email">
                      <strong>From Email *</strong>
                    </label>
                    <input
                      id="smtp-from-email"
                      type="email"
                      className="form-control"
                      value={smtpSettings.from_email}
                      onChange={(e) => handleInputChange('from_email', e.target.value)}
                      placeholder="noreply@yourdomain.com"
                      required
                    />
                    <small className="form-text text-muted">
                      Email address that notifications will be sent from
                    </small>
                  </div>
                </div>

                {/* From Name */}
                <div className="col-md-6">
                  <div className="form-group" style={{ marginBottom: '15px' }}>
                    <label htmlFor="smtp-from-name">
                      <strong>From Name</strong>
                    </label>
                    <input
                      id="smtp-from-name"
                      type="text"
                      className="form-control"
                      value={smtpSettings.from_name}
                      onChange={(e) => handleInputChange('from_name', e.target.value)}
                      placeholder="OpsConductor"
                    />
                    <small className="form-text text-muted">
                      Display name for outgoing emails
                    </small>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div style={{ marginTop: '20px', paddingTop: '20px', borderTop: '1px solid #dee2e6' }}>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={saving}
                  style={{ marginRight: '10px' }}
                >
                  {saving ? 'Saving...' : 'Save Settings'}
                </button>
                
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={fetchSMTPSettings}
                  disabled={loading}
                  style={{ marginRight: '10px' }}
                >
                  Reset
                </button>
              </div>
            </form>
          )}
        </div>
      </div>

      {/* Test SMTP Configuration Card */}
      <div className="card" style={{ marginTop: '20px' }}>
        <div className="card-header">
          <h4>🧪 Test SMTP Configuration</h4>
        </div>
        <div className="card-body">
          <p>Send a test email to verify your SMTP configuration is working correctly.</p>
          
          <div className="form-group" style={{ marginBottom: '15px' }}>
            <label htmlFor="test-email">
              <strong>Test Email Address</strong>
            </label>
            <input
              id="test-email"
              type="email"
              className="form-control"
              value={testEmail}
              onChange={(e) => setTestEmail(e.target.value)}
              placeholder="test@example.com"
              style={{ maxWidth: '400px' }}
            />
          </div>
          
          <button
            className="btn btn-success"
            onClick={testSMTPSettings}
            disabled={testing || !testEmail}
          >
            {testing ? 'Sending Test Email...' : 'Send Test Email'}
          </button>
        </div>
      </div>

      {/* Quick Setup Guide */}
      <div className="card" style={{ marginTop: '20px' }}>
        <div className="card-header">
          <h4>📋 Quick Setup Guide</h4>
        </div>
        <div className="card-body">
          <div className="row">
            <div className="col-md-6">
              <h5>Gmail Setup</h5>
              <ul>
                <li><strong>Host:</strong> smtp.gmail.com</li>
                <li><strong>Port:</strong> 587</li>
                <li><strong>TLS:</strong> Enabled</li>
                <li><strong>Username:</strong> your-email@gmail.com</li>
                <li><strong>Password:</strong> Use App Password (not regular password)</li>
              </ul>
              <small>
                <a href="https://support.google.com/accounts/answer/185833" target="_blank" rel="noopener noreferrer">
                  How to create Gmail App Password →
                </a>
              </small>
            </div>
            
            <div className="col-md-6">
              <h5>Outlook/Office 365 Setup</h5>
              <ul>
                <li><strong>Host:</strong> smtp.office365.com</li>
                <li><strong>Port:</strong> 587</li>
                <li><strong>TLS:</strong> Enabled</li>
                <li><strong>Username:</strong> your-email@outlook.com</li>
                <li><strong>Password:</strong> Your regular password</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;