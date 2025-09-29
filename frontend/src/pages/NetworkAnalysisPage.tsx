import React, { useState, useEffect } from 'react';
import { 
  Network, Plus, Search, Filter, Eye, Edit, Trash2, Play, 
  Activity, AlertTriangle, CheckCircle, Clock, Zap, Brain
} from 'lucide-react';
import { networkApi } from '../services/api';
import { NetworkProbe, NetworkProbeCreate, NetworkAnalysis } from '../types';

const NetworkAnalysisPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'probes' | 'analyses' | 'monitoring'>('probes');
  const [probes, setProbes] = useState<NetworkProbe[]>([]);
  const [analyses, setAnalyses] = useState<NetworkAnalysis[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedProbe, setSelectedProbe] = useState<NetworkProbe | null>(null);
  const [selectedAnalysis, setSelectedAnalysis] = useState<NetworkAnalysis | null>(null);
  const [showAnalysisModal, setShowAnalysisModal] = useState(false);

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const itemsPerPage = 20;

  useEffect(() => {
    if (activeTab === 'probes') {
      loadProbes();
    } else if (activeTab === 'analyses') {
      loadAnalyses();
    }
  }, [activeTab, currentPage, statusFilter]);

  const loadProbes = async () => {
    try {
      setLoading(true);
      const response = await networkApi.listProbes(
        (currentPage - 1) * itemsPerPage,
        itemsPerPage
      );
      setProbes(response.probes);
      setTotalItems(response.total);
    } catch (err: any) {
      setError(err.message || 'Failed to load network probes');
    } finally {
      setLoading(false);
    }
  };

  const loadAnalyses = async () => {
    try {
      setLoading(true);
      const response = await networkApi.listAnalyses(
        (currentPage - 1) * itemsPerPage,
        itemsPerPage
      );
      setAnalyses(response.analyses);
      setTotalItems(response.total);
    } catch (err: any) {
      setError(err.message || 'Failed to load network analyses');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteProbe = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this probe?')) return;
    
    try {
      await networkApi.deleteProbe(id);
      loadProbes();
    } catch (err: any) {
      setError(err.message || 'Failed to delete probe');
    }
  };

  const handleRunProbe = async (id: number) => {
    try {
      await networkApi.runProbe(id);
      loadProbes();
    } catch (err: any) {
      setError(err.message || 'Failed to run probe');
    }
  };

  const getProbeTypeIcon = (type: string) => {
    switch (type) {
      case 'ping': return <Activity className="text-success" size={16} />;
      case 'port_scan': return <Network className="text-info" size={16} />;
      case 'service_discovery': return <Search className="text-warning" size={16} />;
      case 'packet_capture': return <Zap className="text-danger" size={16} />;
      default: return <Network className="text-muted" size={16} />;
    }
  };

  const getStatusBadge = (status: string) => {
    const badges = {
      idle: 'badge bg-secondary',
      running: 'badge bg-primary',
      completed: 'badge bg-success',
      failed: 'badge bg-danger'
    };
    return badges[status as keyof typeof badges] || 'badge bg-secondary';
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running': return <Clock className="text-primary" size={16} />;
      case 'completed': return <CheckCircle className="text-success" size={16} />;
      case 'failed': return <AlertTriangle className="text-danger" size={16} />;
      default: return <Clock className="text-secondary" size={16} />;
    }
  };

  const filteredProbes = probes.filter(probe =>
    probe.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    probe.host.toLowerCase().includes(searchTerm.toLowerCase())
  ).filter(probe => statusFilter === 'all' || probe.status === statusFilter);

  const filteredAnalyses = analyses.filter(analysis =>
    analysis.analysis_type.toLowerCase().includes(searchTerm.toLowerCase())
  ).filter(analysis => statusFilter === 'all' || analysis.status === statusFilter);

  const totalPages = Math.ceil(totalItems / itemsPerPage);

  if (loading && activeTab !== 'monitoring') {
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
                <Network className="me-2" size={24} />
                Network Analysis
              </h1>
              <p className="text-muted mb-0">Monitor and analyze network infrastructure</p>
            </div>
            {activeTab === 'probes' && (
              <button
                className="btn btn-primary"
                onClick={() => setShowCreateModal(true)}
              >
                <Plus size={16} className="me-1" />
                Create Probe
              </button>
            )}
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

          {/* Tabs */}
          <ul className="nav nav-tabs mb-4">
            <li className="nav-item">
              <button
                className={`nav-link ${activeTab === 'probes' ? 'active' : ''}`}
                onClick={() => setActiveTab('probes')}
              >
                <Network size={16} className="me-1" />
                Network Probes
              </button>
            </li>
            <li className="nav-item">
              <button
                className={`nav-link ${activeTab === 'analyses' ? 'active' : ''}`}
                onClick={() => setActiveTab('analyses')}
              >
                <Brain size={16} className="me-1" />
                AI Analysis
              </button>
            </li>
            <li className="nav-item">
              <button
                className={`nav-link ${activeTab === 'monitoring' ? 'active' : ''}`}
                onClick={() => setActiveTab('monitoring')}
              >
                <Activity size={16} className="me-1" />
                Real-time Monitoring
              </button>
            </li>
          </ul>

          {/* Filters */}
          {activeTab !== 'monitoring' && (
            <div className="card mb-4">
              <div className="card-body">
                <div className="row g-3">
                  <div className="col-md-6">
                    <div className="input-group">
                      <span className="input-group-text">
                        <Search size={16} />
                      </span>
                      <input
                        type="text"
                        className="form-control"
                        placeholder={`Search ${activeTab}...`}
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                      />
                    </div>
                  </div>
                  <div className="col-md-4">
                    <select
                      className="form-select"
                      value={statusFilter}
                      onChange={(e) => setStatusFilter(e.target.value)}
                    >
                      <option value="all">All Status</option>
                      <option value="idle">Idle</option>
                      <option value="running">Running</option>
                      <option value="completed">Completed</option>
                      <option value="failed">Failed</option>
                    </select>
                  </div>
                  <div className="col-md-2">
                    <button
                      className="btn btn-outline-secondary w-100"
                      onClick={() => {
                        setSearchTerm('');
                        setStatusFilter('all');
                      }}
                    >
                      <Filter size={16} className="me-1" />
                      Clear
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Tab Content */}
          {activeTab === 'probes' && (
            <ProbesTab
              probes={filteredProbes}
              onEdit={(probe) => {
                setSelectedProbe(probe);
                setShowEditModal(true);
              }}
              onDelete={handleDeleteProbe}
              onRun={handleRunProbe}
            />
          )}

          {activeTab === 'analyses' && (
            <AnalysesTab
              analyses={filteredAnalyses}
              onView={(analysis) => {
                setSelectedAnalysis(analysis);
                setShowAnalysisModal(true);
              }}
            />
          )}

          {activeTab === 'monitoring' && (
            <MonitoringTab />
          )}

          {/* Pagination */}
          {activeTab !== 'monitoring' && totalPages > 1 && (
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

      {/* Create Probe Modal */}
      {showCreateModal && (
        <ProbeModal
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            setShowCreateModal(false);
            loadProbes();
          }}
        />
      )}

      {/* Edit Probe Modal */}
      {showEditModal && selectedProbe && (
        <ProbeModal
          probe={selectedProbe}
          onClose={() => {
            setShowEditModal(false);
            setSelectedProbe(null);
          }}
          onSuccess={() => {
            setShowEditModal(false);
            setSelectedProbe(null);
            loadProbes();
          }}
        />
      )}

      {/* Analysis Details Modal */}
      {showAnalysisModal && selectedAnalysis && (
        <AnalysisDetailsModal
          analysis={selectedAnalysis}
          onClose={() => {
            setShowAnalysisModal(false);
            setSelectedAnalysis(null);
          }}
        />
      )}
    </div>
  );
};

// Probes Tab Component
const ProbesTab: React.FC<{
  probes: NetworkProbe[];
  onEdit: (probe: NetworkProbe) => void;
  onDelete: (id: number) => void;
  onRun: (id: number) => void;
}> = ({ probes, onEdit, onDelete, onRun }) => {
  const getProbeTypeIcon = (type: string) => {
    switch (type) {
      case 'ping': return <Activity className="text-success" size={16} />;
      case 'port_scan': return <Network className="text-info" size={16} />;
      case 'service_discovery': return <Search className="text-warning" size={16} />;
      case 'packet_capture': return <Zap className="text-danger" size={16} />;
      default: return <Network className="text-muted" size={16} />;
    }
  };

  const getStatusBadge = (status: string) => {
    const badges = {
      idle: 'badge bg-secondary',
      running: 'badge bg-primary',
      completed: 'badge bg-success',
      failed: 'badge bg-danger'
    };
    return badges[status as keyof typeof badges] || 'badge bg-secondary';
  };

  return (
    <div className="card">
      <div className="card-body">
        {probes.length === 0 ? (
          <div className="text-center py-5">
            <Network size={48} className="text-muted mb-3" />
            <h5 className="text-muted">No network probes found</h5>
            <p className="text-muted">Create your first probe to start monitoring.</p>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="table table-hover">
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Name</th>
                  <th>Target</th>
                  <th>Status</th>
                  <th>Last Run</th>
                  <th>Next Run</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {probes.map((probe) => (
                  <tr key={probe.id}>
                    <td>
                      <div className="d-flex align-items-center">
                        {getProbeTypeIcon(probe.probe_type)}
                        <span className="ms-2 text-capitalize">
                          {probe.probe_type.replace('_', ' ')}
                        </span>
                      </div>
                    </td>
                    <td>
                      <div>
                        <div className="fw-medium">{probe.name}</div>
                        {probe.description && (
                          <div className="text-muted small">{probe.description}</div>
                        )}
                      </div>
                    </td>
                    <td>
                      <code>{probe.host}{probe.port ? `:${probe.port}` : ''}</code>
                    </td>
                    <td>
                      <span className={getStatusBadge(probe.status)}>
                        {probe.status}
                      </span>
                    </td>
                    <td>
                      <span className="small text-muted">
                        {probe.last_run ? new Date(probe.last_run).toLocaleString() : 'Never'}
                      </span>
                    </td>
                    <td>
                      <span className="small text-muted">
                        {probe.next_run ? new Date(probe.next_run).toLocaleString() : '-'}
                      </span>
                    </td>
                    <td>
                      <div className="btn-group btn-group-sm">
                        <button
                          className="btn btn-outline-success"
                          onClick={() => onRun(probe.id)}
                          title="Run Probe"
                          disabled={probe.status === 'running'}
                        >
                          <Play size={14} />
                        </button>
                        <button
                          className="btn btn-outline-secondary"
                          onClick={() => onEdit(probe)}
                          title="Edit"
                        >
                          <Edit size={14} />
                        </button>
                        <button
                          className="btn btn-outline-danger"
                          onClick={() => onDelete(probe.id)}
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
      </div>
    </div>
  );
};

// Analyses Tab Component
const AnalysesTab: React.FC<{
  analyses: NetworkAnalysis[];
  onView: (analysis: NetworkAnalysis) => void;
}> = ({ analyses, onView }) => {
  const getAnalysisIcon = (type: string) => {
    switch (type) {
      case 'connectivity': return <Network className="text-primary" size={16} />;
      case 'performance': return <Activity className="text-success" size={16} />;
      case 'security': return <AlertTriangle className="text-warning" size={16} />;
      case 'discovery': return <Search className="text-info" size={16} />;
      default: return <Brain className="text-muted" size={16} />;
    }
  };

  const getRiskBadge = (score?: number) => {
    if (!score) return 'badge bg-secondary';
    if (score < 3) return 'badge bg-success';
    if (score < 7) return 'badge bg-warning';
    return 'badge bg-danger';
  };

  const getRiskText = (score?: number) => {
    if (!score) return 'Unknown';
    if (score < 3) return 'Low';
    if (score < 7) return 'Medium';
    return 'High';
  };

  return (
    <div className="card">
      <div className="card-body">
        {analyses.length === 0 ? (
          <div className="text-center py-5">
            <Brain size={48} className="text-muted mb-3" />
            <h5 className="text-muted">No analyses found</h5>
            <p className="text-muted">Run network probes to generate AI-powered analyses.</p>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="table table-hover">
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Probe ID</th>
                  <th>Risk Score</th>
                  <th>Anomalies</th>
                  <th>Status</th>
                  <th>Started</th>
                  <th>Duration</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {analyses.map((analysis) => (
                  <tr key={analysis.id}>
                    <td>
                      <div className="d-flex align-items-center">
                        {getAnalysisIcon(analysis.analysis_type)}
                        <span className="ms-2 text-capitalize">
                          {analysis.analysis_type}
                        </span>
                      </div>
                    </td>
                    <td>
                      <code>{analysis.probe_id}</code>
                    </td>
                    <td>
                      <span className={getRiskBadge(analysis.risk_score)}>
                        {getRiskText(analysis.risk_score)}
                        {analysis.risk_score && ` (${analysis.risk_score}/10)`}
                      </span>
                    </td>
                    <td>
                      {analysis.anomalies_detected ? (
                        <AlertTriangle className="text-warning" size={16} />
                      ) : (
                        <CheckCircle className="text-success" size={16} />
                      )}
                    </td>
                    <td>
                      <span className={`badge ${analysis.status === 'completed' ? 'bg-success' : analysis.status === 'failed' ? 'bg-danger' : 'bg-primary'}`}>
                        {analysis.status}
                      </span>
                    </td>
                    <td>
                      <span className="small text-muted">
                        {new Date(analysis.started_at).toLocaleString()}
                      </span>
                    </td>
                    <td>
                      <span className="small text-muted">
                        {analysis.completed_at ? 
                          `${Math.round((new Date(analysis.completed_at).getTime() - new Date(analysis.started_at).getTime()) / 1000)}s` : 
                          'Running...'
                        }
                      </span>
                    </td>
                    <td>
                      <button
                        className="btn btn-outline-primary btn-sm"
                        onClick={() => onView(analysis)}
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
      </div>
    </div>
  );
};

// Monitoring Tab Component
const MonitoringTab: React.FC = () => {
  const [networkHealth, setNetworkHealth] = useState<any>(null);
  const [networkStats, setNetworkStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMonitoringData();
    const interval = setInterval(loadMonitoringData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const loadMonitoringData = async () => {
    try {
      const [health, stats] = await Promise.all([
        networkApi.getNetworkHealth(),
        networkApi.getNetworkStats()
      ]);
      setNetworkHealth(health);
      setNetworkStats(stats);
    } catch (err: any) {
      console.error('Failed to load monitoring data:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="text-center py-5">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="row">
      <div className="col-md-6">
        <div className="card">
          <div className="card-header">
            <h6 className="card-title mb-0">Network Health</h6>
          </div>
          <div className="card-body">
            {networkHealth ? (
              <div>
                <div className="d-flex justify-content-between align-items-center mb-3">
                  <span>Overall Status</span>
                  <span className={`badge ${networkHealth.overall_status === 'healthy' ? 'bg-success' : 'bg-warning'}`}>
                    {networkHealth.overall_status}
                  </span>
                </div>
                <div className="d-flex justify-content-between align-items-center mb-3">
                  <span>Active Probes</span>
                  <span className="fw-bold">{networkHealth.active_probes || 0}</span>
                </div>
                <div className="d-flex justify-content-between align-items-center">
                  <span>Last Updated</span>
                  <span className="small text-muted">
                    {networkHealth.timestamp ? new Date(networkHealth.timestamp).toLocaleString() : 'Never'}
                  </span>
                </div>
              </div>
            ) : (
              <p className="text-muted">No health data available</p>
            )}
          </div>
        </div>
      </div>
      <div className="col-md-6">
        <div className="card">
          <div className="card-header">
            <h6 className="card-title mb-0">Network Statistics</h6>
          </div>
          <div className="card-body">
            {networkStats ? (
              <div>
                <div className="d-flex justify-content-between align-items-center mb-3">
                  <span>Total Analyses</span>
                  <span className="fw-bold">{networkStats.total_analyses || 0}</span>
                </div>
                <div className="d-flex justify-content-between align-items-center mb-3">
                  <span>Anomalies Detected</span>
                  <span className="fw-bold text-warning">{networkStats.anomalies_count || 0}</span>
                </div>
                <div className="d-flex justify-content-between align-items-center">
                  <span>Average Risk Score</span>
                  <span className="fw-bold">{networkStats.avg_risk_score || 'N/A'}</span>
                </div>
              </div>
            ) : (
              <p className="text-muted">No statistics available</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// Probe Modal Component (Create/Edit)
const ProbeModal: React.FC<{
  probe?: NetworkProbe;
  onClose: () => void;
  onSuccess: () => void;
}> = ({ probe, onClose, onSuccess }) => {
  const isEdit = !!probe;
  const [formData, setFormData] = useState<NetworkProbeCreate>({
    name: probe?.name || '',
    description: probe?.description || '',
    host: probe?.host || '',
    port: probe?.port || undefined,
    probe_type: probe?.probe_type || 'ping',
    configuration: probe?.configuration || {},
    is_active: probe?.is_active ?? true
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (isEdit && probe) {
        await networkApi.updateProbe(probe.id, formData);
      } else {
        await networkApi.createProbe(formData);
      }
      onSuccess();
    } catch (err: any) {
      setError(err.message || `Failed to ${isEdit ? 'update' : 'create'} probe`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
      <div className="modal-dialog modal-lg">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title">
              {isEdit ? 'Edit Network Probe' : 'Create Network Probe'}
            </h5>
            <button type="button" className="btn-close" onClick={onClose}></button>
          </div>
          <form onSubmit={handleSubmit}>
            <div className="modal-body">
              {error && (
                <div className="alert alert-danger">{error}</div>
              )}
              
              <div className="row g-3">
                <div className="col-md-8">
                  <label className="form-label">Name *</label>
                  <input
                    type="text"
                    className="form-control"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    required
                  />
                </div>
                
                <div className="col-md-4">
                  <label className="form-label">Type *</label>
                  <select
                    className="form-select"
                    value={formData.probe_type}
                    onChange={(e) => setFormData({ ...formData, probe_type: e.target.value as any })}
                  >
                    <option value="ping">Ping</option>
                    <option value="port_scan">Port Scan</option>
                    <option value="service_discovery">Service Discovery</option>
                    <option value="packet_capture">Packet Capture</option>
                  </select>
                </div>
                
                <div className="col-12">
                  <label className="form-label">Description</label>
                  <input
                    type="text"
                    className="form-control"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  />
                </div>
                
                <div className="col-md-8">
                  <label className="form-label">Host *</label>
                  <input
                    type="text"
                    className="form-control"
                    value={formData.host}
                    onChange={(e) => setFormData({ ...formData, host: e.target.value })}
                    placeholder="IP address or hostname"
                    required
                  />
                </div>
                
                <div className="col-md-4">
                  <label className="form-label">Port</label>
                  <input
                    type="number"
                    className="form-control"
                    value={formData.port || ''}
                    onChange={(e) => setFormData({ ...formData, port: e.target.value ? parseInt(e.target.value) : undefined })}
                    min="1"
                    max="65535"
                  />
                </div>
                
                <div className="col-12">
                  <div className="form-check">
                    <input
                      className="form-check-input"
                      type="checkbox"
                      checked={formData.is_active}
                      onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    />
                    <label className="form-check-label">
                      Active
                    </label>
                  </div>
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
                    {isEdit ? 'Updating...' : 'Creating...'}
                  </>
                ) : (
                  isEdit ? 'Update Probe' : 'Create Probe'
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

// Analysis Details Modal Component
const AnalysisDetailsModal: React.FC<{
  analysis: NetworkAnalysis;
  onClose: () => void;
}> = ({ analysis, onClose }) => {
  return (
    <div className="modal show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
      <div className="modal-dialog modal-xl">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title">Network Analysis Details</h5>
            <button type="button" className="btn-close" onClick={onClose}></button>
          </div>
          <div className="modal-body">
            <div className="row g-3">
              <div className="col-md-6">
                <label className="form-label fw-bold">Analysis Type</label>
                <p className="text-capitalize">{analysis.analysis_type}</p>
              </div>
              <div className="col-md-6">
                <label className="form-label fw-bold">Probe ID</label>
                <p><code>{analysis.probe_id}</code></p>
              </div>
              <div className="col-md-6">
                <label className="form-label fw-bold">Status</label>
                <p>
                  <span className={`badge ${analysis.status === 'completed' ? 'bg-success' : analysis.status === 'failed' ? 'bg-danger' : 'bg-primary'}`}>
                    {analysis.status}
                  </span>
                </p>
              </div>
              <div className="col-md-6">
                <label className="form-label fw-bold">Risk Score</label>
                <p>
                  {analysis.risk_score ? (
                    <span className={`badge ${analysis.risk_score < 3 ? 'bg-success' : analysis.risk_score < 7 ? 'bg-warning' : 'bg-danger'}`}>
                      {analysis.risk_score}/10
                    </span>
                  ) : (
                    'N/A'
                  )}
                </p>
              </div>
              <div className="col-md-6">
                <label className="form-label fw-bold">Anomalies Detected</label>
                <p>
                  {analysis.anomalies_detected ? (
                    <span className="text-warning">Yes</span>
                  ) : (
                    <span className="text-success">No</span>
                  )}
                </p>
              </div>
              <div className="col-md-6">
                <label className="form-label fw-bold">Started</label>
                <p>{new Date(analysis.started_at).toLocaleString()}</p>
              </div>
              {analysis.ai_insights && (
                <div className="col-12">
                  <label className="form-label fw-bold">AI Insights</label>
                  <div className="alert alert-info">
                    {analysis.ai_insights}
                  </div>
                </div>
              )}
              {analysis.recommendations && analysis.recommendations.length > 0 && (
                <div className="col-12">
                  <label className="form-label fw-bold">Recommendations</label>
                  <ul className="list-group">
                    {analysis.recommendations.map((rec, index) => (
                      <li key={index} className="list-group-item">{rec}</li>
                    ))}
                  </ul>
                </div>
              )}
              <div className="col-12">
                <label className="form-label fw-bold">Results</label>
                <pre className="bg-light p-3 rounded small" style={{ maxHeight: '300px', overflow: 'auto' }}>
                  {JSON.stringify(analysis.results, null, 2)}
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

export default NetworkAnalysisPage;