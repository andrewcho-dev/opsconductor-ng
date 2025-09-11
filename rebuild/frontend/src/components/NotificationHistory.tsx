import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { X, Mail, Link } from 'lucide-react';

interface Notification {
  id: number;
  job_run_id: number;
  channel: string;
  dest: string;
  payload: any;
  status: string;
  sent_at: string | null;
  retries: number;
}

interface NotificationWorkerStatus {
  worker_running: boolean;
  pending_notifications: number;
  failed_notifications: number;
  last_check: string;
}

const Notifications: React.FC = () => {
  const { token } = useAuth();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [workerStatus, setWorkerStatus] = useState<NotificationWorkerStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [showTestForm, setShowTestForm] = useState(false);
  
  // Test notification form
  const [testForm, setTestForm] = useState({
    channel: 'email',
    dest: '',
    message: 'This is a test notification from OpsConductor'
  });

  const fetchNotifications = async (pageNum: number = 1) => {
    try {
      setLoading(true);
      const response = await fetch(`/api/v1/notifications/notifications?offset=${(pageNum - 1) * 10}&limit=10`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setNotifications(data.notifications || []);
      setTotalPages(Math.ceil((data.total || 0) / 10));
      setError(null);
    } catch (err) {
      console.error('Error fetching notifications:', err);
      setError('Failed to fetch notifications');
    } finally {
      setLoading(false);
    }
  };

  const fetchWorkerStatus = async () => {
    try {
      const response = await fetch('/api/v1/notifications/status', {
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
    } catch (err) {
      console.error('Error fetching worker status:', err);
    }
  };

  const controlWorker = async (action: 'start' | 'stop') => {
    try {
      const response = await fetch(`/api/v1/notifications/worker/${action}`, {
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
      const response = await fetch('/api/v1/notifications/notifications/enhanced', {
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
      
      // Refresh notifications
      await fetchNotifications(page);
      
    } catch (err) {
      console.error('Error sending test notification:', err);
      setError('Failed to send test notification');
    }
  };

  useEffect(() => {
    fetchNotifications(page);
    fetchWorkerStatus();
    
    // Set up periodic refresh
    const interval = setInterval(() => {
      fetchWorkerStatus();
    }, 30000); // Refresh every 30 seconds

    return () => clearInterval(interval);
  }, [page, token]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'sent': return '#28a745';
      case 'failed': return '#dc3545';
      case 'pending': return '#ffc107';
      default: return '#6c757d';
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Not sent';
    return new Date(dateString).toLocaleString();
  };

  return (
    <div style={{ padding: '20px' }}>
      <h1>Notification Management</h1>

      {error && (
        <div className="alert alert-danger" style={{ marginBottom: '20px' }}>
          {error}
          <button 
            onClick={() => setError(null)}
            style={{ float: 'right', background: 'none', border: 'none', fontSize: '18px' }}
          >
            <X size={16} />
          </button>
        </div>
      )}

      {/* Worker Status Card */}
      <div className="card" style={{ marginBottom: '20px' }}>
        <div className="card-header">
          <h3>Notification Worker Status</h3>
        </div>
        <div className="card-body">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap' }}>
            <div>
              <span 
                className="badge" 
                style={{ 
                  backgroundColor: workerStatus?.worker_running ? '#28a745' : '#dc3545',
                  color: 'white',
                  padding: '5px 10px',
                  marginRight: '10px'
                }}
              >
                {workerStatus?.worker_running ? 'Running' : 'Stopped'}
              </span>
              <small style={{ color: '#6c757d' }}>
                Last check: {workerStatus?.last_check ? new Date(workerStatus.last_check).toLocaleString() : 'Unknown'}
              </small>
            </div>
            
            <div style={{ margin: '10px 0' }}>
              <span style={{ marginRight: '15px' }}>
                Pending: {workerStatus?.pending_notifications || 0}
              </span>
              <span>
                Failed: {workerStatus?.failed_notifications || 0}
              </span>
            </div>
            
            <div>
              <button
                className="btn btn-primary"
                style={{ marginRight: '10px' }}
                onClick={() => controlWorker(workerStatus?.worker_running ? 'stop' : 'start')}
              >
                {workerStatus?.worker_running ? 'Stop' : 'Start'} Worker
              </button>
              <button
                className="btn btn-secondary"
                onClick={() => {
                  fetchNotifications(page);
                  fetchWorkerStatus();
                }}
              >
                Refresh
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div style={{ marginBottom: '20px' }}>
        <button
          className="btn btn-success"
          style={{ marginRight: '10px' }}
          onClick={() => setShowTestForm(true)}
        >
          Send Test Notification
        </button>
      </div>

      {/* Test Notification Form */}
      {showTestForm && (
        <div className="card" style={{ marginBottom: '20px' }}>
          <div className="card-header">
            <h4>Send Test Notification</h4>
          </div>
          <div className="card-body">
            <div className="form-group" style={{ marginBottom: '15px' }}>
              <label>Channel:</label>
              <select
                className="form-control"
                value={testForm.channel}
                onChange={(e) => setTestForm({ ...testForm, channel: e.target.value })}
              >
                <option value="email">Email</option>
                <option value="webhook">Webhook</option>
              </select>
            </div>
            
            <div className="form-group" style={{ marginBottom: '15px' }}>
              <label>{testForm.channel === 'email' ? 'Email Address:' : 'Webhook URL:'}</label>
              <input
                type="text"
                className="form-control"
                value={testForm.dest}
                onChange={(e) => setTestForm({ ...testForm, dest: e.target.value })}
                required
              />
            </div>
            
            <div className="form-group" style={{ marginBottom: '15px' }}>
              <label>Test Message:</label>
              <textarea
                className="form-control"
                rows={3}
                value={testForm.message}
                onChange={(e) => setTestForm({ ...testForm, message: e.target.value })}
              />
            </div>
            
            <button
              className="btn btn-primary"
              style={{ marginRight: '10px' }}
              onClick={sendTestNotification}
              disabled={!testForm.dest}
            >
              Send Test
            </button>
            <button
              className="btn btn-secondary"
              onClick={() => setShowTestForm(false)}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Notifications Table */}
      <div className="card">
        <div className="card-header">
          <h3>Recent Notifications</h3>
        </div>
        <div className="card-body">
          {loading ? (
            <div style={{ textAlign: 'center', padding: '20px' }}>
              Loading...
            </div>
          ) : (
            <>
              <div className="table-responsive">
                <table className="table table-striped">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Channel</th>
                      <th>Destination</th>
                      <th>Job Run</th>
                      <th>Status</th>
                      <th>Sent At</th>
                      <th>Retries</th>
                    </tr>
                  </thead>
                  <tbody>
                    {notifications.map((notification) => (
                      <tr key={notification.id}>
                        <td>{notification.id}</td>
                        <td>
                          <span style={{ display: 'flex', alignItems: 'center' }}>
                            {notification.channel === 'email' ? <Mail size={14} className="inline mr-1" /> : <Link size={14} className="inline mr-1" />} {notification.channel}
                          </span>
                        </td>
                        <td style={{ maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                          {notification.dest}
                        </td>
                        <td>
                          {notification.job_run_id === 0 ? 'Test' : notification.job_run_id}
                        </td>
                        <td>
                          <span 
                            className="badge"
                            style={{ 
                              backgroundColor: getStatusColor(notification.status),
                              color: 'white',
                              padding: '3px 8px'
                            }}
                          >
                            {notification.status}
                          </span>
                        </td>
                        <td>{formatDate(notification.sent_at)}</td>
                        <td>{notification.retries}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              
              {totalPages > 1 && (
                <div style={{ textAlign: 'center', marginTop: '20px' }}>
                  <div className="btn-group">
                    {Array.from({ length: totalPages }, (_, i) => i + 1).map((pageNum) => (
                      <button
                        key={pageNum}
                        className={`btn ${pageNum === page ? 'btn-primary' : 'btn-outline-primary'}`}
                        onClick={() => setPage(pageNum)}
                      >
                        {pageNum}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default Notifications;