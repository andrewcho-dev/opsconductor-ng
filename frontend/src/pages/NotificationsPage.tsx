import React, { useState, useEffect } from 'react';
import { 
  Bell, Plus, Search, Filter, Eye, Trash2, 
  CheckCircle, AlertCircle, Info, AlertTriangle,
  Clock, Send, User, Users, Globe
} from 'lucide-react';
import { notificationApi } from '../services/api';
import { Notification, NotificationCreate } from '../types';

const NotificationsPage: React.FC = () => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedNotification, setSelectedNotification] = useState<Notification | null>(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const itemsPerPage = 20;

  useEffect(() => {
    loadNotifications();
  }, [currentPage, statusFilter, typeFilter]);

  const loadNotifications = async () => {
    try {
      setLoading(true);
      const filters: any = {};
      if (statusFilter !== 'all') filters.status = statusFilter;
      if (typeFilter !== 'all') filters.recipient = typeFilter;
      
      const response = await notificationApi.list(
        (currentPage - 1) * itemsPerPage,
        itemsPerPage,
        filters
      );
      setNotifications(response.notifications);
      setTotalItems(response.total);
    } catch (err: any) {
      setError(err.message || 'Failed to load notifications');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this notification?')) return;
    
    try {
      await notificationApi.delete(id);
      loadNotifications();
    } catch (err: any) {
      setError(err.message || 'Failed to delete notification');
    }
  };

  // Mark as read functionality not available in backend

  const getNotificationIcon = (status: string) => {
    switch (status) {
      case 'sent': return <CheckCircle className="text-success" size={16} />;
      case 'failed': return <AlertCircle className="text-danger" size={16} />;
      case 'pending': return <Clock className="text-warning" size={16} />;
      default: return <Info className="text-info" size={16} />;
    }
  };

  const getStatusBadge = (status: string) => {
    const badges = {
      pending: 'badge bg-warning',
      sent: 'badge bg-success',
      failed: 'badge bg-danger',
      delivered: 'badge bg-primary'
    };
    return badges[status as keyof typeof badges] || 'badge bg-secondary';
  };

  const getAttemptsBadge = (attempts: number, maxAttempts: number) => {
    if (attempts >= maxAttempts) {
      return 'badge bg-danger';
    } else if (attempts > maxAttempts / 2) {
      return 'badge bg-warning';
    }
    return 'badge bg-info';
  };

  const filteredNotifications = notifications.filter(notification =>
    (notification.subject?.toLowerCase().includes(searchTerm.toLowerCase()) || '') ||
    notification.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
    notification.recipient.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const totalPages = Math.ceil(totalItems / itemsPerPage);

  if (loading) {
    return (
      <div className="container-fluid">
        <div className="d-flex justify-content-center align-items-center" style={{ height: '400px' }}>
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container-fluid">
      <div className="row">
        <div className="col-12">
          <div className="d-flex justify-content-between align-items-center mb-4">
            <div>
              <h1 className="h3 mb-0">
                <Bell className="me-2" size={24} />
                Notifications
              </h1>
              <p className="text-muted mb-0">Manage system notifications and alerts</p>
            </div>
            <div className="d-flex gap-2">
              <button
                className="btn btn-primary"
                onClick={() => setShowCreateModal(true)}
              >
                <Plus size={16} className="me-1" />
                Create Notification
              </button>
            </div>
          </div>

          {error && (
            <div className="alert alert-danger alert-dismissible fade show" role="alert">
              {error}
              <button
                type="button"
                className="btn-close"
                onClick={() => setError(null)}
              ></button>
            </div>
          )}

          {/* Filters */}
          <div className="card mb-4">
            <div className="card-body">
              <div className="row g-3">
                <div className="col-md-4">
                  <div className="input-group">
                    <span className="input-group-text">
                      <Search size={16} />
                    </span>
                    <input
                      type="text"
                      className="form-control"
                      placeholder="Search notifications..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                    />
                  </div>
                </div>
                <div className="col-md-3">
                  <select
                    className="form-select"
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                  >
                    <option value="all">All Statuses</option>
                    <option value="pending">Pending</option>
                    <option value="sent">Sent</option>
                    <option value="failed">Failed</option>
                    <option value="delivered">Delivered</option>
                  </select>
                </div>
                <div className="col-md-3">
                  <select
                    className="form-select"
                    value={typeFilter}
                    onChange={(e) => setTypeFilter(e.target.value)}
                  >
                    <option value="all">All Recipients</option>
                    <option value="user">User</option>
                    <option value="admin">Admin</option>
                    <option value="system">System</option>
                  </select>
                </div>
                <div className="col-md-2">
                  <button
                    className="btn btn-outline-secondary w-100"
                    onClick={() => {
                      setSearchTerm('');
                      setStatusFilter('all');
                      setTypeFilter('all');
                    }}
                  >
                    <Filter size={16} className="me-1" />
                    Clear
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Notifications Table */}
          <div className="card">
            <div className="card-body">
              {filteredNotifications.length === 0 ? (
                <div className="text-center py-5">
                  <Bell size={48} className="text-muted mb-3" />
                  <h5 className="text-muted">No notifications found</h5>
                  <p className="text-muted">Create your first notification to get started.</p>
                </div>
              ) : (
                <div className="table-responsive">
                  <table className="table table-hover">
                    <thead>
                      <tr>
                        <th>Status</th>
                        <th>Subject</th>
                        <th>Message</th>
                        <th>Recipient</th>
                        <th>Attempts</th>
                        <th>Created</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredNotifications.map((notification) => (
                        <tr key={notification.id}>
                          <td>
                            <div className="d-flex align-items-center">
                              {getNotificationIcon(notification.status)}
                              <span className={`ms-2 ${getStatusBadge(notification.status)}`}>
                                {notification.status}
                              </span>
                            </div>
                          </td>
                          <td>
                            <div className="fw-medium">
                              {notification.subject || 'No Subject'}
                            </div>
                          </td>
                          <td>
                            <div className="text-truncate" style={{ maxWidth: '200px' }}>
                              {notification.message}
                            </div>
                          </td>
                          <td>
                            <div className="d-flex align-items-center">
                              <User size={14} className="text-muted me-1" />
                              <span className="small">
                                {notification.recipient}
                              </span>
                            </div>
                          </td>
                          <td>
                            <span className={getAttemptsBadge(notification.attempts, notification.max_attempts)}>
                              {notification.attempts}/{notification.max_attempts}
                            </span>
                          </td>
                          <td>
                            <div className="d-flex align-items-center">
                              <Clock size={14} className="text-muted me-1" />
                              <span className="small">
                                {new Date(notification.created_at).toLocaleDateString()}
                              </span>
                            </div>
                          </td>
                          <td>
                            <div className="btn-group btn-group-sm">
                              <button
                                className="btn btn-outline-primary"
                                onClick={() => {
                                  setSelectedNotification(notification);
                                  setShowDetailsModal(true);
                                }}
                                title="View Details"
                              >
                                <Eye size={14} />
                              </button>
                              <button
                                className="btn btn-outline-danger"
                                onClick={() => handleDelete(notification.id)}
                                title="Delete"
                              >
                                <Trash2 size={14} />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Pagination */}
              {totalPages > 1 && (
                <nav className="mt-4">
                  <ul className="pagination justify-content-center">
                    <li className={`page-item ${currentPage === 1 ? 'disabled' : ''}`}>
                      <button
                        className="page-link"
                        onClick={() => setCurrentPage(currentPage - 1)}
                        disabled={currentPage === 1}
                      >
                        Previous
                      </button>
                    </li>
                    {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                      <li key={page} className={`page-item ${currentPage === page ? 'active' : ''}`}>
                        <button
                          className="page-link"
                          onClick={() => setCurrentPage(page)}
                        >
                          {page}
                        </button>
                      </li>
                    ))}
                    <li className={`page-item ${currentPage === totalPages ? 'disabled' : ''}`}>
                      <button
                        className="page-link"
                        onClick={() => setCurrentPage(currentPage + 1)}
                        disabled={currentPage === totalPages}
                      >
                        Next
                      </button>
                    </li>
                  </ul>
                </nav>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Create Notification Modal */}
      {showCreateModal && (
        <CreateNotificationModal
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            setShowCreateModal(false);
            loadNotifications();
          }}
        />
      )}

      {/* Notification Details Modal */}
      {showDetailsModal && selectedNotification && (
        <NotificationDetailsModal
          notification={selectedNotification}
          onClose={() => {
            setShowDetailsModal(false);
            setSelectedNotification(null);
          }}
        />
      )}
    </div>
  );
};

// Create Notification Modal Component
const CreateNotificationModal: React.FC<{
  onClose: () => void;
  onSuccess: () => void;
}> = ({ onClose, onSuccess }) => {
  const [formData, setFormData] = useState<NotificationCreate>({
    recipient: '',
    subject: '',
    message: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await notificationApi.create(formData);
      onSuccess();
    } catch (err: any) {
      setError(err.message || 'Failed to create notification');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
      <div className="modal-dialog modal-lg">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title">Create Notification</h5>
            <button type="button" className="btn-close" onClick={onClose}></button>
          </div>
          <form onSubmit={handleSubmit}>
            <div className="modal-body">
              {error && (
                <div className="alert alert-danger">{error}</div>
              )}
              
              <div className="row g-3">
                <div className="col-12">
                  <label className="form-label">Recipient *</label>
                  <input
                    type="email"
                    className="form-control"
                    value={formData.recipient}
                    onChange={(e) => setFormData({ ...formData, recipient: e.target.value })}
                    placeholder="Enter recipient email address"
                    required
                  />
                </div>
                
                <div className="col-12">
                  <label className="form-label">Subject</label>
                  <input
                    type="text"
                    className="form-control"
                    value={formData.subject || ''}
                    onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                    placeholder="Enter notification subject"
                  />
                </div>
                
                <div className="col-12">
                  <label className="form-label">Message *</label>
                  <textarea
                    className="form-control"
                    rows={4}
                    value={formData.message}
                    onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                    placeholder="Enter notification message"
                    required
                  />
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button type="button" className="btn btn-secondary" onClick={onClose}>
                Cancel
              </button>
              <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading ? (
                  <>
                    <span className="spinner-border spinner-border-sm me-2"></span>
                    Creating...
                  </>
                ) : (
                  'Create Notification'
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

// Notification Details Modal Component
const NotificationDetailsModal: React.FC<{
  notification: Notification;
  onClose: () => void;
}> = ({ notification, onClose }) => {
  return (
    <div className="modal show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
      <div className="modal-dialog modal-lg">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title">Notification Details</h5>
            <button type="button" className="btn-close" onClick={onClose}></button>
          </div>
          <div className="modal-body">
            <div className="row g-3">
              <div className="col-md-6">
                <label className="form-label fw-bold">Subject</label>
                <p>{notification.subject}</p>
              </div>
              <div className="col-md-6">
                <label className="form-label fw-bold">Recipient</label>
                <p>{notification.recipient}</p>
              </div>
              <div className="col-12">
                <label className="form-label fw-bold">Message</label>
                <p>{notification.message}</p>
              </div>
              <div className="col-md-6">
                <label className="form-label fw-bold">Attempts</label>
                <p>{notification.attempts} / {notification.max_attempts}</p>
              </div>
              <div className="col-md-6">
                <label className="form-label fw-bold">Status</label>
                <p className="text-capitalize">{notification.status}</p>
              </div>
              <div className="col-md-6">
                <label className="form-label fw-bold">Created</label>
                <p>{new Date(notification.created_at).toLocaleString()}</p>
              </div>
              {notification.sent_at && (
                <div className="col-md-6">
                  <label className="form-label fw-bold">Sent</label>
                  <p>{new Date(notification.sent_at).toLocaleString()}</p>
                </div>
              )}
              {notification.error_message && (
                <div className="col-12">
                  <label className="form-label fw-bold">Error Message</label>
                  <p className="text-danger">{notification.error_message}</p>
                </div>
              )}
            </div>
          </div>
          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NotificationsPage;