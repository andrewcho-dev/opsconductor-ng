import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { AlertCircle, Mail, Link, CheckCircle, XCircle, Clock, RefreshCw } from 'lucide-react';

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

const NotificationHistoryPage: React.FC = () => {
  const { user, token } = useAuth();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedNotification, setSelectedNotification] = useState<Notification | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);

  const fetchNotifications = async (pageNum: number = 1) => {
    try {
      setLoading(true);
      const response = await fetch(`/api/v1/notification/notifications?skip=${(pageNum - 1) * 20}&limit=20`, {
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
      setTotal(data.total || 0);
      setTotalPages(Math.ceil((data.total || 0) / 20));
      setError(null);
    } catch (err) {
      console.error('Error fetching notifications:', err);
      setError('Failed to fetch notifications');
      setNotifications([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user?.role === 'admin') {
      fetchNotifications(page);
    }
  }, [page, token, user?.role]);

  const handleNotificationSelect = (notification: Notification) => {
    setSelectedNotification(notification);
  };

  const getStatusIcon = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'sent':
        return <CheckCircle size={14} />;
      case 'failed':
        return <XCircle size={14} />;
      case 'pending':
        return <Clock size={14} />;
      default:
        return <AlertCircle size={14} />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'sent':
        return 'status-badge-success';
      case 'failed':
        return 'status-badge-danger';
      case 'pending':
        return 'status-badge-warning';
      default:
        return 'status-badge-neutral';
    }
  };

  const getChannelIcon = (channel: string) => {
    switch (channel?.toLowerCase()) {
      case 'email':
        return <Mail size={14} />;
      case 'webhook':
      case 'slack':
      case 'teams':
        return <Link size={14} />;
      default:
        return <AlertCircle size={14} />;
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Not sent';
    return new Date(dateString).toLocaleString();
  };

  const handleRefresh = () => {
    fetchNotifications(page);
  };

  if (user?.role !== 'admin') {
    return (
      <div className="dense-dashboard">
        <div className="dashboard-header">
          <div className="header-left">
            <h1>Notification History</h1>
            <p className="header-subtitle">View notification delivery history and status</p>
          </div>
        </div>

        <div className="alert">
          <AlertCircle size={20} style={{ marginRight: '8px' }} />
          <div>
            <strong>Access Restricted</strong><br />
            Only administrators can view notification history.
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="dense-dashboard">
      <style>
        {`
          /* Dashboard-style layout - EXACT MATCH */
          .dense-dashboard {
            padding: 8px 12px;
            max-width: 100%;
            font-size: 13px;
          }
          .dashboard-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid var(--neutral-200);
          }
          .header-left h1 {
            font-size: 18px;
            font-weight: 600;
            margin: 0;
            color: var(--neutral-800);
          }
          .header-subtitle {
            font-size: 12px;
            color: var(--neutral-600);
            margin: 2px 0 0 0;
          }
          .dashboard-grid {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 12px;
            align-items: stretch;
            height: calc(100vh - 110px);
          }
          .dashboard-section {
            background: white;
            border: 1px solid var(--neutral-200);
            border-radius: 6px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            height: 100%;
          }
          .section-header {
            background: var(--neutral-50);
            padding: 8px 12px;
            font-weight: 600;
            font-size: 13px;
            color: var(--neutral-700);
            border-bottom: 1px solid var(--neutral-200);
            display: flex;
            justify-content: space-between;
            align-items: center;
          }
          .compact-content {
            padding: 0;
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: auto;
          }
          .table-container {
            flex: 1;
            overflow: auto;
          }
          
          /* Notifications table styles */
          .notifications-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
          }
          .notifications-table th {
            background: var(--neutral-50);
            padding: 6px 8px;
            text-align: left;
            font-weight: 600;
            color: var(--neutral-700);
            border-bottom: 1px solid var(--neutral-200);
            font-size: 11px;
          }
          .notifications-table td {
            padding: 6px 8px;
            border-bottom: 1px solid var(--neutral-100);
            vertical-align: middle;
            font-size: 12px;
          }
          .notifications-table tr:hover {
            background: var(--neutral-50);
          }
          .notifications-table tr.selected {
            background: var(--primary-blue-light);
            border-left: 3px solid var(--primary-blue);
          }
          .notifications-table tr {
            cursor: pointer;
          }
          
          /* Details panel */
          .details-panel {
            padding: 8px;
          }
          .details-panel h3 {
            margin: 0 0 12px 0;
            font-size: 14px;
            font-weight: 600;
            color: var(--neutral-800);
          }
          .detail-group {
            margin-bottom: 12px;
          }
          .detail-label {
            font-size: 10px;
            font-weight: 600;
            color: var(--neutral-500);
            margin-bottom: 3px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
          }
          .detail-value {
            font-size: 12px;
            color: var(--neutral-800);
            padding: 6px 0;
            border-bottom: 1px solid var(--neutral-100);
            word-wrap: break-word;
          }
          
          /* Button styles */
          .btn-icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 24px;
            height: 24px;
            border: none;
            background: none;
            cursor: pointer;
            transition: all 0.15s;
            margin: 0 1px;
            padding: 2px;
            border-radius: 3px;
          }
          .btn-icon:hover {
            background: var(--neutral-100);
          }
          .btn-icon:disabled {
            opacity: 0.3;
            cursor: not-allowed;
          }
          .btn-success {
            color: var(--success-green);
          }
          .btn-success:hover:not(:disabled) {
            color: var(--success-green-dark);
          }
          
          .empty-state {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 40px 20px;
            text-align: center;
            color: var(--neutral-500);
            height: 100%;
          }
          .empty-state h3 {
            margin: 0 0 8px 0;
            font-size: 14px;
            font-weight: 600;
          }
          .empty-state p {
            margin: 0;
            font-size: 12px;
          }
          
          .alert {
            background: var(--danger-red-light);
            color: var(--danger-red);
            padding: 8px 12px;
            border-radius: 4px;
            margin-bottom: 12px;
            font-size: 12px;
            display: flex;
            align-items: center;
          }
          
          .notification-status-icon {
            display: inline-flex;
            align-items: center;
            gap: 4px;
          }
          
          .notification-channel-icon {
            display: inline-flex;
            align-items: center;
            gap: 4px;
          }
          
          .pagination {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 4px;
            padding: 8px;
            border-top: 1px solid var(--neutral-200);
            background: var(--neutral-50);
          }
          
          .pagination button {
            padding: 4px 8px;
            border: 1px solid var(--neutral-300);
            background: white;
            color: var(--neutral-700);
            border-radius: 3px;
            cursor: pointer;
            font-size: 11px;
          }
          
          .pagination button:hover {
            background: var(--neutral-100);
          }
          
          .pagination button.active {
            background: var(--primary-blue);
            color: white;
            border-color: var(--primary-blue);
          }
          
          .pagination button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
          }
        `}
      </style>
      
      {/* Dashboard-style header */}
      <div className="dashboard-header">
        <div className="header-left">
          <h1>Notification History</h1>
          <p className="header-subtitle">View notification delivery history and status</p>
        </div>
        <div className="header-actions">
          <button 
            className="btn-icon btn-success"
            onClick={handleRefresh}
            title="Refresh notifications"
            disabled={loading}
          >
            <RefreshCw size={16} />
          </button>
        </div>
      </div>

      {error && (
        <div className="alert">
          <AlertCircle size={20} style={{ marginRight: '8px' }} />
          {error}
          <button 
            style={{ marginLeft: 'auto', background: 'none', border: 'none', color: 'inherit', cursor: 'pointer' }}
            onClick={() => setError(null)}
          >
            ×
          </button>
        </div>
      )}

      {/* 2-column dashboard grid */}
      <div className="dashboard-grid">
        {/* Column 1: Notifications */}
        <div className="dashboard-section">
          <div className="section-header">
            Notification History ({total})
            <button 
              className="btn-icon btn-success"
              onClick={handleRefresh}
              title="Refresh notifications"
              disabled={loading}
            >
              <RefreshCw size={14} />
            </button>
          </div>
          <div className="compact-content">
            {loading ? (
              <div className="empty-state">
                <div className="loading-spinner"></div>
                <p>Loading notifications...</p>
              </div>
            ) : notifications.length === 0 ? (
              <div className="empty-state">
                <h3>No notifications found</h3>
                <p>No notification history available. Notifications will appear here once jobs start sending them.</p>
              </div>
            ) : (
              <>
                <div className="table-container">
                  <table className="notifications-table">
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
                        <tr 
                          key={notification.id} 
                          className={selectedNotification?.id === notification.id ? 'selected' : ''}
                          onClick={() => handleNotificationSelect(notification)}
                        >
                          <td>
                            <div style={{ fontWeight: '500' }}>#{notification.id}</div>
                          </td>
                          <td>
                            <div className="notification-channel-icon">
                              {getChannelIcon(notification.channel)}
                              <span>{notification.channel}</span>
                            </div>
                          </td>
                          <td style={{ maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                            {notification.dest}
                          </td>
                          <td>
                            {notification.job_run_id === 0 ? (
                              <span style={{ color: 'var(--neutral-500)', fontStyle: 'italic' }}>Test</span>
                            ) : (
                              <span>#{notification.job_run_id}</span>
                            )}
                          </td>
                          <td>
                            <div className="notification-status-icon">
                              {getStatusIcon(notification.status)}
                              <span className={`status-badge ${getStatusBadge(notification.status)}`}>
                                {notification.status}
                              </span>
                            </div>
                          </td>
                          <td style={{ fontSize: '11px', color: 'var(--neutral-500)' }}>
                            {formatDate(notification.sent_at)}
                          </td>
                          <td>
                            {notification.retries > 0 ? (
                              <span style={{ color: 'var(--warning-orange)' }}>{notification.retries}</span>
                            ) : (
                              <span style={{ color: 'var(--neutral-500)' }}>{notification.retries}</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                
                {totalPages > 1 && (
                  <div className="pagination">
                    <button 
                      onClick={() => setPage(page - 1)} 
                      disabled={page === 1}
                    >
                      Previous
                    </button>
                    {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => {
                      const pageNum = totalPages <= 7 ? i + 1 : 
                        page <= 4 ? i + 1 :
                        page >= totalPages - 3 ? totalPages - 6 + i :
                        page - 3 + i;
                      return (
                        <button
                          key={pageNum}
                          className={pageNum === page ? 'active' : ''}
                          onClick={() => setPage(pageNum)}
                        >
                          {pageNum}
                        </button>
                      );
                    })}
                    <button 
                      onClick={() => setPage(page + 1)} 
                      disabled={page === totalPages}
                    >
                      Next
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        </div>

        {/* Column 2: Details Panel */}
        <div className="dashboard-section">
          <div className="section-header">
            {selectedNotification ? 'Notification Details' : 'Select Notification'}
          </div>
          <div className="compact-content">
            {selectedNotification ? (
              <div className="details-panel">
                <h3>Notification #{selectedNotification.id}</h3>
                
                <div className="detail-group">
                  <div className="detail-label">Channel</div>
                  <div className="detail-value">
                    <div className="notification-channel-icon">
                      {getChannelIcon(selectedNotification.channel)}
                      <span>{selectedNotification.channel}</span>
                    </div>
                  </div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">Destination</div>
                  <div className="detail-value">{selectedNotification.dest}</div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">Status</div>
                  <div className="detail-value">
                    <div className="notification-status-icon">
                      {getStatusIcon(selectedNotification.status)}
                      <span className={`status-badge ${getStatusBadge(selectedNotification.status)}`}>
                        {selectedNotification.status}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">Job Run ID</div>
                  <div className="detail-value">
                    {selectedNotification.job_run_id === 0 ? 'Test Notification' : `#${selectedNotification.job_run_id}`}
                  </div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">Sent At</div>
                  <div className="detail-value">{formatDate(selectedNotification.sent_at)}</div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">Retry Count</div>
                  <div className="detail-value">
                    {selectedNotification.retries} 
                    {selectedNotification.retries > 0 && (
                      <span style={{ color: 'var(--warning-orange)', marginLeft: '8px' }}>
                        (retried)
                      </span>
                    )}
                  </div>
                </div>

                {selectedNotification.payload && (
                  <div className="detail-group">
                    <div className="detail-label">Payload Preview</div>
                    <div className="detail-value">
                      <pre style={{ fontSize: '10px', color: 'var(--neutral-600)', maxHeight: '100px', overflow: 'auto' }}>
                        {JSON.stringify(selectedNotification.payload, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="empty-state">
                <p>Select a notification to view details</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default NotificationHistoryPage;