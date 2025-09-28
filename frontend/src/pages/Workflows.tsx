import React, { useState, useEffect } from 'react';
import { 
  Play, 
  Pause, 
  Square, 
  Clock, 
  CheckCircle, 
  XCircle, 
  AlertCircle,
  Plus,
  Search,
  MoreVertical,
  GitBranch,
  Activity
} from 'lucide-react';

interface Flow {
  id: string;
  name: string;
  description: string;
  status: 'active' | 'paused' | 'disabled';
  lastRun: string | null;
  nextRun: string | null;
  runCount: number;
  successRate: number;
  tags: string[];
  created: string;
  createdBy: string;
}

interface FlowRun {
  id: string;
  flowId: string;
  flowName: string;
  status: 'running' | 'completed' | 'failed' | 'cancelled' | 'pending';
  startTime: string;
  endTime: string | null;
  duration: number | null;
  triggeredBy: string;
}

const Workflows: React.FC = () => {
  const [flows, setFlows] = useState<Flow[]>([]);
  const [recentRuns, setRecentRuns] = useState<FlowRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [activeTab, setActiveTab] = useState<'flows' | 'runs'>('flows');

  useEffect(() => {
    // TODO: Replace with actual Prefect API calls
    const mockFlows: Flow[] = [
      {
        id: '1',
        name: 'Data Pipeline ETL',
        description: 'Extract, transform, and load data from multiple sources',
        status: 'active',
        lastRun: '2024-01-15T10:30:00Z',
        nextRun: '2024-01-16T10:30:00Z',
        runCount: 145,
        successRate: 98.5,
        tags: ['etl', 'data', 'scheduled'],
        created: '2024-01-01T00:00:00Z',
        createdBy: 'admin'
      },
      {
        id: '2',
        name: 'System Health Check',
        description: 'Monitor system resources and alert on anomalies',
        status: 'active',
        lastRun: '2024-01-15T11:00:00Z',
        nextRun: '2024-01-15T12:00:00Z',
        runCount: 2880,
        successRate: 99.2,
        tags: ['monitoring', 'health', 'alerts'],
        created: '2024-01-01T00:00:00Z',
        createdBy: 'admin'
      },
      {
        id: '3',
        name: 'Backup Workflow',
        description: 'Automated backup of critical system data',
        status: 'paused',
        lastRun: '2024-01-14T02:00:00Z',
        nextRun: null,
        runCount: 30,
        successRate: 100,
        tags: ['backup', 'maintenance'],
        created: '2024-01-01T00:00:00Z',
        createdBy: 'admin'
      }
    ];

    const mockRuns: FlowRun[] = [
      {
        id: '1',
        flowId: '1',
        flowName: 'Data Pipeline ETL',
        status: 'completed',
        startTime: '2024-01-15T10:30:00Z',
        endTime: '2024-01-15T10:45:00Z',
        duration: 900,
        triggeredBy: 'schedule'
      },
      {
        id: '2',
        flowId: '2',
        flowName: 'System Health Check',
        status: 'running',
        startTime: '2024-01-15T11:00:00Z',
        endTime: null,
        duration: null,
        triggeredBy: 'schedule'
      },
      {
        id: '3',
        flowId: '1',
        flowName: 'Data Pipeline ETL',
        status: 'failed',
        startTime: '2024-01-14T10:30:00Z',
        endTime: '2024-01-14T10:35:00Z',
        duration: 300,
        triggeredBy: 'manual'
      }
    ];

    setTimeout(() => {
      setFlows(mockFlows);
      setRecentRuns(mockRuns);
      setLoading(false);
    }, 1000);
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
      case 'running':
        return <Play className="text-success" size={16} />;
      case 'paused':
        return <Pause className="text-warning" size={16} />;
      case 'disabled':
        return <Square className="text-secondary" size={16} />;
      case 'completed':
        return <CheckCircle className="text-success" size={16} />;
      case 'failed':
        return <XCircle className="text-danger" size={16} />;
      case 'cancelled':
        return <Square className="text-secondary" size={16} />;
      case 'pending':
        return <Clock className="text-warning" size={16} />;
      default:
        return <AlertCircle className="text-secondary" size={16} />;
    }
  };

  const getStatusBadge = (status: string) => {
    const baseClass = "badge rounded-pill";
    switch (status) {
      case 'active':
        return `${baseClass} bg-success`;
      case 'paused':
        return `${baseClass} bg-warning`;
      case 'disabled':
        return `${baseClass} bg-secondary`;
      case 'running':
        return `${baseClass} bg-primary`;
      case 'completed':
        return `${baseClass} bg-success`;
      case 'failed':
        return `${baseClass} bg-danger`;
      case 'cancelled':
        return `${baseClass} bg-secondary`;
      case 'pending':
        return `${baseClass} bg-warning`;
      default:
        return `${baseClass} bg-secondary`;
    }
  };

  const formatDuration = (seconds: number | null) => {
    if (!seconds) return '-';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  const formatDateTime = (dateString: string | null) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString();
  };

  const filteredFlows = flows.filter(flow => {
    const matchesSearch = flow.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         flow.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || flow.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  if (loading) {
    return (
      <div className="container-fluid py-4">
        <div className="d-flex justify-content-center align-items-center" style={{ minHeight: '400px' }}>
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container-fluid py-4">
      <div className="row mb-4">
        <div className="col">
          <div className="d-flex justify-content-between align-items-center">
            <div>
              <h1 className="h3 mb-1">Workflows</h1>
              <p className="text-muted mb-0">Manage and monitor your Prefect flows</p>
            </div>
            <button className="btn btn-primary">
              <Plus size={16} className="me-2" />
              Create Flow
            </button>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="row mb-4">
        <div className="col-md-3">
          <div className="card border-0 shadow-sm">
            <div className="card-body">
              <div className="d-flex align-items-center">
                <div className="flex-shrink-0">
                  <GitBranch className="text-primary" size={24} />
                </div>
                <div className="flex-grow-1 ms-3">
                  <div className="fw-semibold">Total Flows</div>
                  <div className="h4 mb-0">{flows.length}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div className="col-md-3">
          <div className="card border-0 shadow-sm">
            <div className="card-body">
              <div className="d-flex align-items-center">
                <div className="flex-shrink-0">
                  <Play className="text-success" size={24} />
                </div>
                <div className="flex-grow-1 ms-3">
                  <div className="fw-semibold">Active Flows</div>
                  <div className="h4 mb-0">{flows.filter(f => f.status === 'active').length}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div className="col-md-3">
          <div className="card border-0 shadow-sm">
            <div className="card-body">
              <div className="d-flex align-items-center">
                <div className="flex-shrink-0">
                  <Activity className="text-info" size={24} />
                </div>
                <div className="flex-grow-1 ms-3">
                  <div className="fw-semibold">Running Now</div>
                  <div className="h4 mb-0">{recentRuns.filter(r => r.status === 'running').length}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div className="col-md-3">
          <div className="card border-0 shadow-sm">
            <div className="card-body">
              <div className="d-flex align-items-center">
                <div className="flex-shrink-0">
                  <CheckCircle className="text-success" size={24} />
                </div>
                <div className="flex-grow-1 ms-3">
                  <div className="fw-semibold">Success Rate</div>
                  <div className="h4 mb-0">
                    {flows.length > 0 ? Math.round(flows.reduce((acc, f) => acc + f.successRate, 0) / flows.length) : 0}%
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="card border-0 shadow-sm">
        <div className="card-header bg-white border-bottom">
          <ul className="nav nav-tabs card-header-tabs">
            <li className="nav-item">
              <button 
                className={`nav-link ${activeTab === 'flows' ? 'active' : ''}`}
                onClick={() => setActiveTab('flows')}
              >
                <GitBranch size={16} className="me-2" />
                Flows
              </button>
            </li>
            <li className="nav-item">
              <button 
                className={`nav-link ${activeTab === 'runs' ? 'active' : ''}`}
                onClick={() => setActiveTab('runs')}
              >
                <Activity size={16} className="me-2" />
                Recent Runs
              </button>
            </li>
          </ul>
        </div>

        <div className="card-body">
          {activeTab === 'flows' && (
            <>
              {/* Search and Filter */}
              <div className="row mb-3">
                <div className="col-md-6">
                  <div className="input-group">
                    <span className="input-group-text bg-white border-end-0">
                      <Search size={16} className="text-muted" />
                    </span>
                    <input
                      type="text"
                      className="form-control border-start-0"
                      placeholder="Search flows..."
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
                    <option value="all">All Status</option>
                    <option value="active">Active</option>
                    <option value="paused">Paused</option>
                    <option value="disabled">Disabled</option>
                  </select>
                </div>
              </div>

              {/* Flows Table */}
              <div className="table-responsive">
                <table className="table table-hover">
                  <thead>
                    <tr>
                      <th>Flow</th>
                      <th>Status</th>
                      <th>Last Run</th>
                      <th>Next Run</th>
                      <th>Success Rate</th>
                      <th>Total Runs</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredFlows.map((flow) => (
                      <tr key={flow.id}>
                        <td>
                          <div>
                            <div className="fw-semibold">{flow.name}</div>
                            <div className="text-muted small">{flow.description}</div>
                            <div className="mt-1">
                              {flow.tags.map((tag) => (
                                <span key={tag} className="badge bg-light text-dark me-1 small">
                                  {tag}
                                </span>
                              ))}
                            </div>
                          </div>
                        </td>
                        <td>
                          <span className={getStatusBadge(flow.status)}>
                            {getStatusIcon(flow.status)}
                            <span className="ms-1">{flow.status}</span>
                          </span>
                        </td>
                        <td>
                          <div className="small">
                            {formatDateTime(flow.lastRun)}
                          </div>
                        </td>
                        <td>
                          <div className="small">
                            {formatDateTime(flow.nextRun)}
                          </div>
                        </td>
                        <td>
                          <div className="d-flex align-items-center">
                            <div className="progress me-2" style={{ width: '60px', height: '6px' }}>
                              <div 
                                className="progress-bar bg-success" 
                                style={{ width: `${flow.successRate}%` }}
                              ></div>
                            </div>
                            <span className="small">{flow.successRate}%</span>
                          </div>
                        </td>
                        <td>{flow.runCount.toLocaleString()}</td>
                        <td>
                          <div className="dropdown">
                            <button 
                              className="btn btn-sm btn-outline-secondary"
                              data-bs-toggle="dropdown"
                            >
                              <MoreVertical size={14} />
                            </button>
                            <ul className="dropdown-menu">
                              <li><button className="dropdown-item" type="button">Run Now</button></li>
                              <li><button className="dropdown-item" type="button">Edit</button></li>
                              <li><button className="dropdown-item" type="button">View Runs</button></li>
                              <li><hr className="dropdown-divider" /></li>
                              <li><button className="dropdown-item text-warning" type="button">
                                {flow.status === 'active' ? 'Pause' : 'Resume'}
                              </button></li>
                              <li><button className="dropdown-item text-danger" type="button">Delete</button></li>
                            </ul>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}

          {activeTab === 'runs' && (
            <div className="table-responsive">
              <table className="table table-hover">
                <thead>
                  <tr>
                    <th>Flow</th>
                    <th>Status</th>
                    <th>Started</th>
                    <th>Duration</th>
                    <th>Triggered By</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {recentRuns.map((run) => (
                    <tr key={run.id}>
                      <td>
                        <div className="fw-semibold">{run.flowName}</div>
                        <div className="text-muted small">Run ID: {run.id}</div>
                      </td>
                      <td>
                        <span className={getStatusBadge(run.status)}>
                          {getStatusIcon(run.status)}
                          <span className="ms-1">{run.status}</span>
                        </span>
                      </td>
                      <td>
                        <div className="small">
                          {formatDateTime(run.startTime)}
                        </div>
                      </td>
                      <td>
                        <div className="small">
                          {formatDuration(run.duration)}
                        </div>
                      </td>
                      <td>
                        <span className="badge bg-light text-dark">
                          {run.triggeredBy}
                        </span>
                      </td>
                      <td>
                        <div className="dropdown">
                          <button 
                            className="btn btn-sm btn-outline-secondary"
                            data-bs-toggle="dropdown"
                          >
                            <MoreVertical size={14} />
                          </button>
                          <ul className="dropdown-menu">
                            <li><button className="dropdown-item" type="button">View Details</button></li>
                            <li><button className="dropdown-item" type="button">View Logs</button></li>
                            {run.status === 'running' && (
                              <li><button className="dropdown-item text-danger" type="button">Cancel</button></li>
                            )}
                          </ul>
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
    </div>
  );
};

export default Workflows;