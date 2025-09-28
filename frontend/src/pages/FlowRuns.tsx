import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Play, 
  Square, 
  Clock, 
  CheckCircle, 
  XCircle, 
  AlertCircle,
  Search,
  MoreVertical,
  ArrowLeft,
  Activity,
  Download,
  RefreshCw
} from 'lucide-react';

interface FlowRun {
  id: string;
  flowId: string;
  flowName: string;
  status: 'running' | 'completed' | 'failed' | 'cancelled' | 'pending' | 'crashed';
  startTime: string;
  endTime: string | null;
  duration: number | null;
  triggeredBy: string;
  parameters: Record<string, any>;
  logs: string[];
  taskRuns: TaskRun[];
}

interface TaskRun {
  id: string;
  name: string;
  status: 'running' | 'completed' | 'failed' | 'pending' | 'skipped';
  startTime: string;
  endTime: string | null;
  duration: number | null;
}

const FlowRuns: React.FC = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [runs, setRuns] = useState<FlowRun[]>([]);
  const [selectedRun, setSelectedRun] = useState<FlowRun | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [activeTab, setActiveTab] = useState<'overview' | 'logs' | 'tasks'>('overview');

  useEffect(() => {
    // TODO: Replace with actual Prefect API calls
    const mockRuns: FlowRun[] = [
      {
        id: '1',
        flowId: '1',
        flowName: 'Data Pipeline ETL',
        status: 'completed',
        startTime: '2024-01-15T10:30:00Z',
        endTime: '2024-01-15T10:45:00Z',
        duration: 900,
        triggeredBy: 'schedule',
        parameters: { source: 'database', target: 'warehouse' },
        logs: [
          '2024-01-15T10:30:00Z - Starting ETL process',
          '2024-01-15T10:32:00Z - Extracting data from source',
          '2024-01-15T10:38:00Z - Transforming data',
          '2024-01-15T10:43:00Z - Loading data to warehouse',
          '2024-01-15T10:45:00Z - ETL process completed successfully'
        ],
        taskRuns: [
          {
            id: '1-1',
            name: 'extract_data',
            status: 'completed',
            startTime: '2024-01-15T10:30:00Z',
            endTime: '2024-01-15T10:32:00Z',
            duration: 120
          },
          {
            id: '1-2',
            name: 'transform_data',
            status: 'completed',
            startTime: '2024-01-15T10:32:00Z',
            endTime: '2024-01-15T10:38:00Z',
            duration: 360
          },
          {
            id: '1-3',
            name: 'load_data',
            status: 'completed',
            startTime: '2024-01-15T10:38:00Z',
            endTime: '2024-01-15T10:43:00Z',
            duration: 300
          }
        ]
      },
      {
        id: '2',
        flowId: '2',
        flowName: 'System Health Check',
        status: 'running',
        startTime: '2024-01-15T11:00:00Z',
        endTime: null,
        duration: null,
        triggeredBy: 'schedule',
        parameters: { check_type: 'full' },
        logs: [
          '2024-01-15T11:00:00Z - Starting health check',
          '2024-01-15T11:01:00Z - Checking CPU usage',
          '2024-01-15T11:02:00Z - Checking memory usage'
        ],
        taskRuns: [
          {
            id: '2-1',
            name: 'check_cpu',
            status: 'completed',
            startTime: '2024-01-15T11:01:00Z',
            endTime: '2024-01-15T11:01:30Z',
            duration: 30
          },
          {
            id: '2-2',
            name: 'check_memory',
            status: 'running',
            startTime: '2024-01-15T11:02:00Z',
            endTime: null,
            duration: null
          },
          {
            id: '2-3',
            name: 'check_disk',
            status: 'pending',
            startTime: '',
            endTime: null,
            duration: null
          }
        ]
      },
      {
        id: '3',
        flowId: '1',
        flowName: 'Data Pipeline ETL',
        status: 'failed',
        startTime: '2024-01-14T10:30:00Z',
        endTime: '2024-01-14T10:35:00Z',
        duration: 300,
        triggeredBy: 'manual',
        parameters: { source: 'database', target: 'warehouse' },
        logs: [
          '2024-01-14T10:30:00Z - Starting ETL process',
          '2024-01-14T10:32:00Z - Extracting data from source',
          '2024-01-14T10:35:00Z - ERROR: Connection timeout to warehouse'
        ],
        taskRuns: [
          {
            id: '3-1',
            name: 'extract_data',
            status: 'completed',
            startTime: '2024-01-14T10:30:00Z',
            endTime: '2024-01-14T10:32:00Z',
            duration: 120
          },
          {
            id: '3-2',
            name: 'transform_data',
            status: 'completed',
            startTime: '2024-01-14T10:32:00Z',
            endTime: '2024-01-14T10:34:00Z',
            duration: 120
          },
          {
            id: '3-3',
            name: 'load_data',
            status: 'failed',
            startTime: '2024-01-14T10:34:00Z',
            endTime: '2024-01-14T10:35:00Z',
            duration: 60
          }
        ]
      }
    ];

    setTimeout(() => {
      setRuns(mockRuns);
      if (id) {
        const run = mockRuns.find(r => r.id === id);
        setSelectedRun(run || null);
      }
      setLoading(false);
    }, 1000);
  }, [id]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <Play className="text-primary" size={16} />;
      case 'completed':
        return <CheckCircle className="text-success" size={16} />;
      case 'failed':
      case 'crashed':
        return <XCircle className="text-danger" size={16} />;
      case 'cancelled':
        return <Square className="text-secondary" size={16} />;
      case 'pending':
        return <Clock className="text-warning" size={16} />;
      case 'skipped':
        return <AlertCircle className="text-info" size={16} />;
      default:
        return <AlertCircle className="text-secondary" size={16} />;
    }
  };

  const getStatusBadge = (status: string) => {
    const baseClass = "badge rounded-pill";
    switch (status) {
      case 'running':
        return `${baseClass} bg-primary`;
      case 'completed':
        return `${baseClass} bg-success`;
      case 'failed':
      case 'crashed':
        return `${baseClass} bg-danger`;
      case 'cancelled':
        return `${baseClass} bg-secondary`;
      case 'pending':
        return `${baseClass} bg-warning`;
      case 'skipped':
        return `${baseClass} bg-info`;
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

  const filteredRuns = runs.filter(run => {
    const matchesSearch = run.flowName.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         run.id.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || run.status === statusFilter;
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

  if (selectedRun) {
    return (
      <div className="container-fluid py-4">
        <div className="row mb-4">
          <div className="col">
            <div className="d-flex align-items-center mb-3">
              <button 
                className="btn btn-outline-secondary me-3"
                onClick={() => {
                  setSelectedRun(null);
                  navigate('/workflows/runs');
                }}
              >
                <ArrowLeft size={16} />
              </button>
              <div>
                <h1 className="h3 mb-1">Flow Run Details</h1>
                <p className="text-muted mb-0">{selectedRun.flowName} - Run {selectedRun.id}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Run Status Card */}
        <div className="row mb-4">
          <div className="col">
            <div className="card border-0 shadow-sm">
              <div className="card-body">
                <div className="row">
                  <div className="col-md-3">
                    <div className="d-flex align-items-center mb-2">
                      {getStatusIcon(selectedRun.status)}
                      <span className={`ms-2 ${getStatusBadge(selectedRun.status)}`}>
                        {selectedRun.status.toUpperCase()}
                      </span>
                    </div>
                    <div className="small text-muted">Status</div>
                  </div>
                  <div className="col-md-3">
                    <div className="fw-semibold mb-1">{formatDateTime(selectedRun.startTime)}</div>
                    <div className="small text-muted">Started</div>
                  </div>
                  <div className="col-md-3">
                    <div className="fw-semibold mb-1">{formatDuration(selectedRun.duration)}</div>
                    <div className="small text-muted">Duration</div>
                  </div>
                  <div className="col-md-3">
                    <div className="fw-semibold mb-1">{selectedRun.triggeredBy}</div>
                    <div className="small text-muted">Triggered By</div>
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
                  className={`nav-link ${activeTab === 'overview' ? 'active' : ''}`}
                  onClick={() => setActiveTab('overview')}
                >
                  <Activity size={16} className="me-2" />
                  Overview
                </button>
              </li>
              <li className="nav-item">
                <button 
                  className={`nav-link ${activeTab === 'tasks' ? 'active' : ''}`}
                  onClick={() => setActiveTab('tasks')}
                >
                  <CheckCircle size={16} className="me-2" />
                  Tasks ({selectedRun.taskRuns.length})
                </button>
              </li>
              <li className="nav-item">
                <button 
                  className={`nav-link ${activeTab === 'logs' ? 'active' : ''}`}
                  onClick={() => setActiveTab('logs')}
                >
                  <Download size={16} className="me-2" />
                  Logs
                </button>
              </li>
            </ul>
          </div>

          <div className="card-body">
            {activeTab === 'overview' && (
              <div className="row">
                <div className="col-md-6">
                  <h5 className="mb-3">Parameters</h5>
                  <div className="table-responsive">
                    <table className="table table-sm">
                      <tbody>
                        {Object.entries(selectedRun.parameters).map(([key, value]) => (
                          <tr key={key}>
                            <td className="fw-semibold">{key}</td>
                            <td>{JSON.stringify(value)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
                <div className="col-md-6">
                  <h5 className="mb-3">Task Summary</h5>
                  <div className="row">
                    {['completed', 'running', 'failed', 'pending'].map(status => {
                      const count = selectedRun.taskRuns.filter(t => t.status === status).length;
                      return (
                        <div key={status} className="col-6 mb-3">
                          <div className="card bg-light border-0">
                            <div className="card-body p-3">
                              <div className="d-flex align-items-center">
                                {getStatusIcon(status)}
                                <div className="ms-2">
                                  <div className="fw-semibold">{count}</div>
                                  <div className="small text-muted">{status}</div>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'tasks' && (
              <div className="table-responsive">
                <table className="table table-hover">
                  <thead>
                    <tr>
                      <th>Task</th>
                      <th>Status</th>
                      <th>Started</th>
                      <th>Duration</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedRun.taskRuns.map((task) => (
                      <tr key={task.id}>
                        <td>
                          <div className="fw-semibold">{task.name}</div>
                          <div className="text-muted small">ID: {task.id}</div>
                        </td>
                        <td>
                          <span className={getStatusBadge(task.status)}>
                            {getStatusIcon(task.status)}
                            <span className="ms-1">{task.status}</span>
                          </span>
                        </td>
                        <td>
                          <div className="small">
                            {formatDateTime(task.startTime)}
                          </div>
                        </td>
                        <td>
                          <div className="small">
                            {formatDuration(task.duration)}
                          </div>
                        </td>
                        <td>
                          <button className="btn btn-sm btn-outline-primary">
                            View Logs
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {activeTab === 'logs' && (
              <div>
                <div className="d-flex justify-content-between align-items-center mb-3">
                  <h5 className="mb-0">Flow Logs</h5>
                  <button className="btn btn-sm btn-outline-primary">
                    <Download size={14} className="me-1" />
                    Download
                  </button>
                </div>
                <div className="bg-dark text-light p-3 rounded" style={{ fontFamily: 'monospace', fontSize: '0.875rem', maxHeight: '400px', overflowY: 'auto' }}>
                  {selectedRun.logs.map((log, index) => (
                    <div key={index} className="mb-1">
                      {log}
                    </div>
                  ))}
                </div>
              </div>
            )}
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
              <h1 className="h3 mb-1">Flow Runs</h1>
              <p className="text-muted mb-0">Monitor and manage flow execution history</p>
            </div>
            <button className="btn btn-outline-primary">
              <RefreshCw size={16} className="me-2" />
              Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="row mb-4">
        {['running', 'completed', 'failed', 'pending'].map(status => {
          const count = runs.filter(r => r.status === status).length;
          return (
            <div key={status} className="col-md-3 mb-3">
              <div className="card border-0 shadow-sm">
                <div className="card-body">
                  <div className="d-flex align-items-center">
                    <div className="flex-shrink-0">
                      {getStatusIcon(status)}
                    </div>
                    <div className="flex-grow-1 ms-3">
                      <div className="fw-semibold text-capitalize">{status}</div>
                      <div className="h4 mb-0">{count}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Search and Filter */}
      <div className="card border-0 shadow-sm">
        <div className="card-body">
          <div className="row mb-3">
            <div className="col-md-6">
              <div className="input-group">
                <span className="input-group-text bg-white border-end-0">
                  <Search size={16} className="text-muted" />
                </span>
                <input
                  type="text"
                  className="form-control border-start-0"
                  placeholder="Search runs..."
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
                <option value="running">Running</option>
                <option value="completed">Completed</option>
                <option value="failed">Failed</option>
                <option value="pending">Pending</option>
              </select>
            </div>
          </div>

          {/* Runs Table */}
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
                {filteredRuns.map((run) => (
                  <tr key={run.id} style={{ cursor: 'pointer' }} onClick={() => setSelectedRun(run)}>
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
                      <div className="dropdown" onClick={(e) => e.stopPropagation()}>
                        <button 
                          className="btn btn-sm btn-outline-secondary"
                          data-bs-toggle="dropdown"
                        >
                          <MoreVertical size={14} />
                        </button>
                        <ul className="dropdown-menu">
                          <li><button className="dropdown-item" type="button" onClick={() => setSelectedRun(run)}>View Details</button></li>
                          <li><button className="dropdown-item" type="button">View Logs</button></li>
                          {run.status === 'running' && (
                            <li><button className="dropdown-item text-danger" type="button">Cancel</button></li>
                          )}
                          {run.status === 'failed' && (
                            <li><button className="dropdown-item" type="button">Retry</button></li>
                          )}
                        </ul>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FlowRuns;