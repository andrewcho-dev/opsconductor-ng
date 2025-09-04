import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { X, RefreshCw, Play, Square, AlertCircle } from 'lucide-react';

interface WorkerStatusData {
  worker_running: boolean;
  pending_notifications: number;
  failed_notifications: number;
  last_check: string;
}

const NotificationWorkerStatus: React.FC = () => {
  const { token } = useAuth();
  const [workerStatus, setWorkerStatus] = useState<WorkerStatusData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showTestForm, setShowTestForm] = useState(false);
  
  // Test notification form
  const [testForm, setTestForm] = useState({
    channel: 'email',
    dest: '',
    message: 'This is a test notification from OpsConductor'
  });

  const fetchWorkerStatus = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/notification/status', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setWorkerStatus(data);
      setError(null);
    } catch (err) {
      console.error('Error fetching worker status:', err);
      setError('Failed to fetch worker status');
    } finally {
      setLoading(false);
    }
  };

  const controlWorker = async (action: 'start' | 'stop') => {
    try {
      const response = await fetch(`/api/v1/notification/worker/${action}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Refresh worker status
      await fetchWorkerStatus();
    } catch (err) {
      console.error(`Error ${action}ing worker:`, err);
      setError(`Failed to ${action} notification worker`);
    }
  };

  const sendTestNotification = async () => {
    try {
      const response = await fetch('/api/v1/notification/notifications/enhanced', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          job_run_id: 0, // Test notification
          channel: testForm.channel,
          dest: testForm.dest,
          payload: {
            job_name: 'Test Notification',
            status: 'succeeded',
            message: testForm.message,
            test: true
          }
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      setShowTestForm(false);
      setTestForm({ channel: 'email', dest: '', message: 'This is a test notification from OpsConductor' });
      
      // Show success message
      setError(null);
      
    } catch (err) {
      console.error('Error sending test notification:', err);
      setError('Failed to send test notification');
    }
  };

  useEffect(() => {
    fetchWorkerStatus();
    
    // Set up periodic refresh
    const interval = setInterval(() => {
      fetchWorkerStatus();
    }, 30000); // Refresh every 30 seconds

    return () => clearInterval(interval);
  }, [token]);

  return (
    <div className="settings-section">
      <style>
        {`
          .worker-status-card {
            background: white;
            border: 1px solid var(--neutral-200);
            border-radius: 6px;
            margin-bottom: 16px;
          }
          
          .worker-status-header {
            background: var(--neutral-50);
            padding: 12px 16px;
            font-weight: 600;
            font-size: 14px;
            color: var(--neutral-700);
            border-bottom: 1px solid var(--neutral-200);
            border-radius: 6px 6px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
          }
          
          .worker-status-body {
            padding: 16px;
          }
          
          .status-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
            margin-bottom: 16px;
          }
          
          .status-info {
            display: flex;
            align-items: center;
            gap: 12px;
            flex: 1;
            min-width: 0;
          }
          
          .status-badge {
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            color: white;
          }
          
          .status-badge.running {
            background: var(--success-green);
          }
          
          .status-badge.stopped {
            background: var(--danger-red);
          }
          
          .status-meta {
            font-size: 11px;
            color: var(--neutral-500);
          }
          
          .status-stats {
            display: flex;
            gap: 16px;
            font-size: 12px;
          }
          
          .stat-item {
            color: var(--neutral-600);
          }
          
          .stat-value {
            font-weight: 600;
            color: var(--neutral-800);
          }
          
          .status-actions {
            display: flex;
            gap: 8px;
            flex-shrink: 0;
          }
          
          .btn {
            padding: 6px 12px;
            border: 1px solid var(--neutral-300);
            background: white;
            color: var(--neutral-700);
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            transition: all 0.15s;
          }
          
          .btn:hover {
            background: var(--neutral-100);
          }
          
          .btn.btn-primary {
            background: var(--primary-blue);
            color: white;
            border-color: var(--primary-blue);
          }
          
          .btn.btn-primary:hover {
            background: var(--primary-blue-dark);
            border-color: var(--primary-blue-dark);
          }
          
          .btn.btn-success {
            background: var(--success-green);
            color: white;
            border-color: var(--success-green);
          }
          
          .btn.btn-success:hover {
            background: var(--success-green-dark);
            border-color: var(--success-green-dark);
          }
          
          .btn.btn-danger {
            background: var(--danger-red);
            color: white;
            border-color: var(--danger-red);
          }
          
          .btn.btn-danger:hover {
            background: var(--danger-red-dark);
            border-color: var(--danger-red-dark);
          }
          
          .test-form {
            background: var(--neutral-50);
            border: 1px solid var(--neutral-200);
            border-radius: 6px;
            padding: 16px;
            margin-top: 16px;
          }
          
          .form-group {
            margin-bottom: 12px;
          }
          
          .form-label {
            display: block;
            font-size: 12px;
            font-weight: 600;
            color: var(--neutral-700);
            margin-bottom: 4px;
          }
          
          .form-control {
            width: 100%;
            padding: 6px 8px;
            border: 1px solid var(--neutral-300);
            border-radius: 4px;
            font-size: 12px;
            background: white;
          }
          
          .form-control:focus {
            outline: none;
            border-color: var(--primary-blue);
            box-shadow: 0 0 0 2px var(--primary-blue-light);
          }
          
          .alert {
            padding: 8px 12px;
            border-radius: 4px;
            margin-bottom: 12px;
            font-size: 12px;
            display: flex;
            align-items: center;
          }
          
          .alert.alert-danger {
            background: var(--danger-red-light);
            color: var(--danger-red);
            border: 1px solid var(--danger-red-light);
          }
          
          .loading-spinner {
            display: inline-block;
            width: 16px;
            height: 16px;
            border: 2px solid var(--neutral-300);
            border-radius: 50%;
            border-top-color: var(--primary-blue);
            animation: spin 1s ease-in-out infinite;
          }
          
          @keyframes spin {
            to { transform: rotate(360deg); }
          }
        `}
      </style>

      <div className="worker-status-card">
        <div className="worker-status-header">
          <span>Notification Worker Status</span>
          <button 
            className="btn"
            onClick={fetchWorkerStatus}
            disabled={loading}
            title="Refresh status"
          >
            {loading ? <div className="loading-spinner"></div> : <RefreshCw size={14} />}
          </button>
        </div>
        <div className="worker-status-body">
          {error && (
            <div className="alert alert-danger">
              <AlertCircle size={16} style={{ marginRight: '8px' }} />
              {error}
              <button 
                style={{ marginLeft: 'auto', background: 'none', border: 'none', color: 'inherit', cursor: 'pointer' }}
                onClick={() => setError(null)}
              >
                <X size={16} />
              </button>
            </div>
          )}

          <div className="status-row">
            <div className="status-info">
              <span className={`status-badge ${workerStatus?.worker_running ? 'running' : 'stopped'}`}>
                {workerStatus?.worker_running ? 'Running' : 'Stopped'}
              </span>
              <div className="status-meta">
                Last check: {workerStatus?.last_check ? new Date(workerStatus.last_check).toLocaleString() : 'Unknown'}
              </div>
            </div>
            
            <div className="status-stats">
              <div className="stat-item">
                Pending: <span className="stat-value">{workerStatus?.pending_notifications || 0}</span>
              </div>
              <div className="stat-item">
                Failed: <span className="stat-value">{workerStatus?.failed_notifications || 0}</span>
              </div>
            </div>
            
            <div className="status-actions">
              <button
                className={`btn ${workerStatus?.worker_running ? 'btn-danger' : 'btn-success'}`}
                onClick={() => controlWorker(workerStatus?.worker_running ? 'stop' : 'start')}
                disabled={loading}
              >
                {workerStatus?.worker_running ? (
                  <>
                    <Square size={14} />
                    Stop
                  </>
                ) : (
                  <>
                    <Play size={14} />
                    Start
                  </>
                )}
              </button>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              className="btn btn-primary"
              onClick={() => setShowTestForm(!showTestForm)}
            >
              {showTestForm ? 'Cancel Test' : 'Send Test Notification'}
            </button>
          </div>

          {showTestForm && (
            <div className="test-form">
              <h4 style={{ margin: '0 0 12px 0', fontSize: '13px', fontWeight: '600' }}>
                Send Test Notification
              </h4>
              
              <div className="form-group">
                <label className="form-label">Channel:</label>
                <select
                  className="form-control"
                  value={testForm.channel}
                  onChange={(e) => setTestForm({ ...testForm, channel: e.target.value })}
                >
                  <option value="email">Email</option>
                  <option value="webhook">Webhook</option>
                </select>
              </div>
              
              <div className="form-group">
                <label className="form-label">
                  {testForm.channel === 'email' ? 'Email Address:' : 'Webhook URL:'}
                </label>
                <input
                  type="text"
                  className="form-control"
                  value={testForm.dest}
                  onChange={(e) => setTestForm({ ...testForm, dest: e.target.value })}
                  placeholder={testForm.channel === 'email' ? 'user@example.com' : 'https://hooks.slack.com/...'}
                  required
                />
              </div>
              
              <div className="form-group">
                <label className="form-label">Test Message:</label>
                <textarea
                  className="form-control"
                  rows={2}
                  value={testForm.message}
                  onChange={(e) => setTestForm({ ...testForm, message: e.target.value })}
                />
              </div>
              
              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  className="btn btn-success"
                  onClick={sendTestNotification}
                  disabled={!testForm.dest}
                >
                  Send Test
                </button>
                <button
                  className="btn"
                  onClick={() => setShowTestForm(false)}
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default NotificationWorkerStatus;