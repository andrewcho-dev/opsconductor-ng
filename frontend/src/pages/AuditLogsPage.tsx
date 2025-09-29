import React, { useState, useEffect } from 'react';
import { 
  Shield, Search, Filter, Download, Eye, 
  CheckCircle, XCircle, Clock, User, Activity
} from 'lucide-react';
import { auditApi } from '../services/api';
import { AuditLog } from '../types';

const AuditLogsPage: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  // Status filter removed - not available in backend
  const [resourceFilter, setResourceFilter] = useState<string>('all');
  const [actionFilter, setActionFilter] = useState<string>('all');
  const [dateRange, setDateRange] = useState({ start: '', end: '' });
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const itemsPerPage = 50;

  // Unique values for filters
  const [resourceTypes, setResourceTypes] = useState<string[]>([]);
  const [actions, setActions] = useState<string[]>([]);

  useEffect(() => {
    loadLogs();
  }, [currentPage, resourceFilter, actionFilter, dateRange]);

  const loadLogs = async () => {
    try {
      setLoading(true);
      const filters: any = {};
      if (resourceFilter !== 'all') filters.entity_type = resourceFilter;
      if (actionFilter !== 'all') filters.action = actionFilter;
      if (dateRange.start) filters.start_date = dateRange.start;
      if (dateRange.end) filters.end_date = dateRange.end;
      
      const response = await auditApi.list(
        (currentPage - 1) * itemsPerPage,
        itemsPerPage,
        filters
      );
      setLogs(response.audit_logs);
      setTotalItems(response.total);

      // Extract unique values for filters
      const uniqueResources = [...new Set(response.audit_logs.map(log => log.entity_type))];
      const uniqueActions = [...new Set(response.audit_logs.map(log => log.action))];
      setResourceTypes(uniqueResources);
      setActions(uniqueActions);
    } catch (err: any) {
      setError(err.message || 'Failed to load audit logs');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    try {
      const filters: any = {};
      if (resourceFilter !== 'all') filters.entity_type = resourceFilter;
      if (actionFilter !== 'all') filters.action = actionFilter;
      if (dateRange.start) filters.start_date = dateRange.start;
      if (dateRange.end) filters.end_date = dateRange.end;

      const blob = await auditApi.export(filters);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `audit-logs-${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      setError(err.message || 'Failed to export audit logs');
    }
  };

  // Status functions removed - status field not available in backend

  const filteredLogs = logs.filter(log =>
    log.action.toLowerCase().includes(searchTerm.toLowerCase()) ||
    log.entity_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (log.entity_id && log.entity_id.toLowerCase().includes(searchTerm.toLowerCase()))
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
                <Shield className="me-2" size={24} />
                Audit Logs
              </h1>
              <p className="text-muted mb-0">System activity and security audit trail</p>
            </div>
            <button
              className="btn btn-outline-primary"
              onClick={handleExport}
            >
              <Download size={16} className="me-1" />
              Export Logs
            </button>
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
                <div className="col-md-3">
                  <div className="input-group">
                    <span className="input-group-text">
                      <Search size={16} />
                    </span>
                    <input
                      type="text"
                      className="form-control"
                      placeholder="Search logs..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                    />
                  </div>
                </div>
                {/* Status filter removed - not available in backend */}
                <div className="col-md-2">
                  <select
                    className="form-select"
                    value={resourceFilter}
                    onChange={(e) => setResourceFilter(e.target.value)}
                  >
                    <option value="all">All Resources</option>
                    {resourceTypes.map(type => (
                      <option key={type} value={type}>{type}</option>
                    ))}
                  </select>
                </div>
                <div className="col-md-2">
                  <select
                    className="form-select"
                    value={actionFilter}
                    onChange={(e) => setActionFilter(e.target.value)}
                  >
                    <option value="all">All Actions</option>
                    {actions.map(action => (
                      <option key={action} value={action}>{action}</option>
                    ))}
                  </select>
                </div>
                <div className="col-md-2">
                  <input
                    type="date"
                    className="form-control"
                    value={dateRange.start}
                    onChange={(e) => setDateRange({ ...dateRange, start: e.target.value })}
                    placeholder="Start Date"
                  />
                </div>
                <div className="col-md-1">
                  <button
                    className="btn btn-outline-secondary w-100"
                    onClick={() => {
                      setSearchTerm('');
                      setResourceFilter('all');
                      setActionFilter('all');
                      setDateRange({ start: '', end: '' });
                    }}
                  >
                    <Filter size={16} />
                  </button>
                </div>
              </div>
              {dateRange.start && (
                <div className="row g-3 mt-2">
                  <div className="col-md-2 offset-md-8">
                    <input
                      type="date"
                      className="form-control"
                      value={dateRange.end}
                      onChange={(e) => setDateRange({ ...dateRange, end: e.target.value })}
                      placeholder="End Date"
                      min={dateRange.start}
                    />
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Audit Logs Table */}
          <div className="card">
            <div className="card-body">
              {filteredLogs.length === 0 ? (
                <div className="text-center py-5">
                  <Shield size={48} className="text-muted mb-3" />
                  <h5 className="text-muted">No audit logs found</h5>
                  <p className="text-muted">No logs match your current filters.</p>
                </div>
              ) : (
                <div className="table-responsive">
                  <table className="table table-hover">
                    <thead>
                      <tr>
                        <th>Event Type</th>
                        <th>Timestamp</th>
                        <th>User</th>
                        <th>Action</th>
                        <th>Entity Type</th>
                        <th>Entity ID</th>
                        <th>IP Address</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredLogs.map((log) => (
                        <tr key={log.id}>
                          <td>
                            <div className="d-flex align-items-center">
                              <Activity size={14} className="text-muted me-1" />
                              <span className="fw-medium text-capitalize">
                                {log.event_type}
                              </span>
                            </div>
                          </td>
                          <td>
                            <div className="d-flex align-items-center">
                              <Clock size={14} className="text-muted me-1" />
                              <span className="small">
                                {new Date(log.created_at).toLocaleString()}
                              </span>
                            </div>
                          </td>
                          <td>
                            <div className="d-flex align-items-center">
                              <User size={14} className="text-muted me-1" />
                              <span>{log.user_id ? `User ${log.user_id}` : 'System'}</span>
                            </div>
                          </td>
                          <td>
                            <div className="d-flex align-items-center">
                              <Activity size={14} className="text-muted me-1" />
                              <span className="fw-medium">{log.action}</span>
                            </div>
                          </td>
                          <td>
                            <span className="badge bg-light text-dark">
                              {log.entity_type}
                            </span>
                          </td>
                          <td>
                            <code className="small">
                              {log.entity_id || '-'}
                            </code>
                          </td>
                          <td>
                            <span className="small text-muted">
                              {log.ip_address || '-'}
                            </span>
                          </td>
                          <td>
                            <button
                              className="btn btn-outline-primary btn-sm"
                              onClick={() => {
                                setSelectedLog(log);
                                setShowDetailsModal(true);
                              }}
                              title="View Details"
                            >
                              <Eye size={14} />
                            </button>
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
                    {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                      const page = Math.max(1, Math.min(totalPages - 4, currentPage - 2)) + i;
                      return (
                        <li key={page} className={`page-item ${currentPage === page ? 'active' : ''}`}>
                          <button
                            className="page-link"
                            onClick={() => setCurrentPage(page)}
                          >
                            {page}
                          </button>
                        </li>
                      );
                    })}
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

      {/* Log Details Modal */}
      {showDetailsModal && selectedLog && (
        <LogDetailsModal
          log={selectedLog}
          onClose={() => {
            setShowDetailsModal(false);
            setSelectedLog(null);
          }}
        />
      )}
    </div>
  );
};

// Log Details Modal Component
const LogDetailsModal: React.FC<{
  log: AuditLog;
  onClose: () => void;
}> = ({ log, onClose }) => {
  return (
    <div className="modal show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
      <div className="modal-dialog modal-lg">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title">Audit Log Details</h5>
            <button type="button" className="btn-close" onClick={onClose}></button>
          </div>
          <div className="modal-body">
            <div className="row g-3">
              {/* Status field removed - not available in backend */}
              <div className="col-md-6">
                <label className="form-label fw-bold">Timestamp</label>
                <p>{new Date(log.created_at).toLocaleString()}</p>
              </div>
              <div className="col-md-6">
                <label className="form-label fw-bold">User</label>
                <p>{log.user_id ? `User ID: ${log.user_id}` : 'System'}</p>
              </div>
              <div className="col-md-6">
                <label className="form-label fw-bold">User ID</label>
                <p>{log.user_id || '-'}</p>
              </div>
              <div className="col-md-6">
                <label className="form-label fw-bold">Action</label>
                <p className="fw-medium">{log.action}</p>
              </div>
              <div className="col-md-6">
                <label className="form-label fw-bold">Entity Type</label>
                <p><span className="badge bg-light text-dark">{log.entity_type}</span></p>
              </div>
              <div className="col-md-6">
                <label className="form-label fw-bold">Entity ID</label>
                <p><code>{log.entity_id || '-'}</code></p>
              </div>
              <div className="col-md-6">
                <label className="form-label fw-bold">IP Address</label>
                <p>{log.ip_address || '-'}</p>
              </div>
              {log.user_agent && (
                <div className="col-12">
                  <label className="form-label fw-bold">User Agent</label>
                  <p className="small text-muted">{log.user_agent}</p>
                </div>
              )}

              <div className="col-12">
                <label className="form-label fw-bold">Details</label>
                <pre className="bg-light p-3 rounded small" style={{ maxHeight: '300px', overflow: 'auto' }}>
                  {JSON.stringify(log.details, null, 2)}
                </pre>
              </div>
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

export default AuditLogsPage;