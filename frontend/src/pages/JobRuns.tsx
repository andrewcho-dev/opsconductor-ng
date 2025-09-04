import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { jobRunApi, jobApi } from '../services/api';
import { JobRun, JobRunStep, Job } from '../types';
import { Plus, Play, CheckCircle, XCircle, Clock, AlertCircle, Pause, ExternalLink, Filter, X } from 'lucide-react';

const JobRuns: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [runs, setRuns] = useState<JobRun[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedJobId, setSelectedJobId] = useState<number | undefined>(undefined);
  const [selectedRun, setSelectedRun] = useState<JobRun | null>(null);
  const [runSteps, setRunSteps] = useState<JobRunStep[]>([]);
  const [loadingSteps, setLoadingSteps] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Parse job_id from URL parameters on mount
  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    const jobIdParam = searchParams.get('job_id');
    if (jobIdParam) {
      const jobId = parseInt(jobIdParam, 10);
      if (!isNaN(jobId)) {
        setSelectedJobId(jobId);
      }
    }
  }, [location.search]);

  useEffect(() => {
    fetchRuns();
    fetchJobs();
  }, [selectedJobId]);

  useEffect(() => {
    if (selectedRun) {
      fetchRunSteps(selectedRun.id);
    }
  }, [selectedRun]);

  const fetchRuns = async () => {
    try {
      setLoading(true);
      const response = await jobRunApi.list(0, 100, selectedJobId);
      setRuns(response.runs || []);
    } catch (error: any) {
      console.error('Failed to fetch job runs:', error);
      setError(error.message || 'Failed to load job runs');
    } finally {
      setLoading(false);
    }
  };

  const fetchJobs = async () => {
    try {
      const response = await jobApi.list(0, 100, false); // Include inactive jobs
      setJobs(response.jobs || []);
    } catch (error: any) {
      console.error('Failed to fetch jobs:', error);
    }
  };

  const fetchRunSteps = async (runId: number) => {
    try {
      setLoadingSteps(true);
      const response = await jobRunApi.getSteps(runId);
      setRunSteps(response || []);
    } catch (error: any) {
      console.error('Failed to fetch run steps:', error);
      setRunSteps([]);
    } finally {
      setLoadingSteps(false);
    }
  };

  const getJobName = (jobId: number) => {
    const job = jobs.find(j => j.id === jobId);
    return job ? job.name : `Job ${jobId}`;
  };

  const getRunStatusBadge = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'succeeded':
      case 'completed':
        return 'status-badge-success';
      case 'failed':
      case 'error':
        return 'status-badge-danger';
      case 'running':
        return 'status-badge-info';
      case 'queued':
      case 'pending':
        return 'status-badge-warning';
      case 'canceled':
      case 'cancelled':
      case 'aborted':
        return 'status-badge-neutral';
      default:
        return 'status-badge-neutral';
    }
  };

  const getRunStatusIcon = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'succeeded':
      case 'completed':
        return <CheckCircle size={14} />;
      case 'failed':
      case 'error':
        return <XCircle size={14} />;
      case 'running':
        return <Play size={14} />;
      case 'queued':
      case 'pending':
        return <Clock size={14} />;
      case 'canceled':
      case 'cancelled':
      case 'aborted':
        return <Pause size={14} />;
      default:
        return <AlertCircle size={14} />;
    }
  };

  const formatDuration = (started?: string, finished?: string) => {
    if (!started) return '-';
    
    const startTime = new Date(started);
    const endTime = finished ? new Date(finished) : new Date();
    const durationMs = endTime.getTime() - startTime.getTime();
    
    const seconds = Math.floor(durationMs / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes % 60}m`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    } else {
      return `${seconds}s`;
    }
  };

  const handleRunSelect = (run: JobRun) => {
    setSelectedRun(run);
  };

  const getFilteredJobName = () => {
    if (!selectedJobId) return 'All Jobs';
    const job = jobs.find(j => j.id === selectedJobId);
    return job ? job.name : `Job ${selectedJobId}`;
  };

  if (loading && runs.length === 0) {
    return (
      <div className="loading-overlay">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  return (
    <div className="dense-dashboard">
      <style>
        {`
          /* Dashboard-style layout - 2/3, 1/3 format */
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
          
          /* Filter bar */
          .filter-bar {
            background: var(--neutral-50);
            padding: 8px 12px;
            border-bottom: 1px solid var(--neutral-200);
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 12px;
          }
          .filter-select {
            padding: 4px 8px;
            border: 1px solid var(--neutral-300);
            border-radius: 4px;
            font-size: 12px;
            background: white;
            min-width: 150px;
          }
          .filter-select:focus {
            outline: none;
            border-color: var(--primary-blue);
          }
          
          /* Job runs table styles */
          .runs-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
          }
          .runs-table th {
            background: var(--neutral-50);
            padding: 6px 8px;
            text-align: left;
            font-weight: 600;
            color: var(--neutral-700);
            border-bottom: 1px solid var(--neutral-200);
            font-size: 11px;
          }
          .runs-table td {
            padding: 6px 8px;
            border-bottom: 1px solid var(--neutral-100);
            vertical-align: middle;
            font-size: 12px;
          }
          .runs-table tr:hover {
            background: var(--neutral-50);
          }
          .runs-table tr.selected {
            background: var(--primary-blue-light);
            border-left: 3px solid var(--primary-blue);
          }
          .runs-table tr {
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
          }
          
          /* Steps section */
          .steps-section {
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px solid var(--neutral-200);
          }
          .step-item {
            background: var(--neutral-50);
            border: 1px solid var(--neutral-200);
            border-radius: 4px;
            padding: 8px;
            margin-bottom: 8px;
          }
          .step-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 6px;
          }
          .step-title {
            font-size: 12px;
            font-weight: 600;
            color: var(--neutral-800);
          }
          .step-details {
            font-size: 11px;
            color: var(--neutral-600);
            line-height: 1.4;
          }
          .step-output {
            background: var(--neutral-100);
            border: 1px solid var(--neutral-200);
            border-radius: 3px;
            padding: 6px;
            margin-top: 6px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 10px;
            max-height: 100px;
            overflow: auto;
          }
          .step-error {
            background: var(--danger-red-light);
            border: 1px solid var(--danger-red);
            color: var(--danger-red);
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
          }
          .btn-icon:hover {
            opacity: 0.7;
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
          .btn-danger {
            color: var(--danger-red);
          }
          .btn-danger:hover:not(:disabled) {
            color: var(--danger-red);
          }
          .btn-ghost {
            color: var(--neutral-500);
          }
          .btn-ghost:hover:not(:disabled) {
            color: var(--neutral-700);
          }
          .btn-primary {
            background: var(--primary-blue);
            color: white;
            padding: 6px 12px;
            border: none;
            border-radius: 4px;
            font-size: 12px;
            cursor: pointer;
          }
          .btn-primary:hover:not(:disabled) {
            background: var(--primary-blue-dark);
          }
          .btn-primary:disabled {
            opacity: 0.5;
            cursor: not-allowed;
          }
          
          .action-buttons {
            display: flex;
            gap: 4px;
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px solid var(--neutral-200);
          }
          
          .empty-state {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 150px;
            color: var(--neutral-500);
            text-align: center;
          }
          .empty-state h3 {
            margin: 0 0 6px 0;
            font-size: 14px;
            font-weight: 600;
          }
          .empty-state p {
            margin: 0 0 12px 0;
            font-size: 12px;
          }
          
          .status-badge {
            display: inline-block;
            padding: 2px 6px;
            border-radius: 12px;
            font-size: 10px;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
          }
          .status-badge-success {
            background: var(--success-green-light);
            color: var(--success-green);
          }
          .status-badge-danger {
            background: var(--danger-red-light);
            color: var(--danger-red);
          }
          .status-badge-warning {
            background: var(--warning-yellow-light);
            color: var(--warning-yellow);
          }
          .status-badge-info {
            background: var(--primary-blue-light);
            color: var(--primary-blue);
          }
          .status-badge-neutral {
            background: var(--neutral-200);
            color: var(--neutral-600);
          }
          
          .alert {
            background: var(--danger-red-light);
            color: var(--danger-red);
            padding: 8px 12px;
            border-radius: 4px;
            margin-bottom: 12px;
            font-size: 12px;
          }
          
          .run-status-icon {
            display: inline-flex;
            align-items: center;
            gap: 4px;
          }
          
          .filter-icon {
            color: var(--neutral-500);
          }
          
          .parameters-json {
            background: var(--neutral-100);
            border: 1px solid var(--neutral-200);
            border-radius: 3px;
            padding: 6px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 10px;
            max-height: 100px;
            overflow: auto;
            white-space: pre-wrap;
          }
        `}
      </style>
      
      {/* Dashboard-style header */}
      <div className="dashboard-header">
        <div className="header-left">
          <h1>Job Runs</h1>
          <p className="header-subtitle">Monitor job execution history and detailed run information</p>
        </div>
        <div className="header-actions">
          <Link 
            to="/job-management"
            className="btn-icon btn-success"
            title="Create new job"
          >
            <Plus size={16} />
          </Link>
        </div>
      </div>

      {error && (
        <div className="alert">
          {error}
          <button 
            style={{ float: 'right', background: 'none', border: 'none', color: 'inherit', cursor: 'pointer' }}
            onClick={() => setError(null)}
          >
            ×
          </button>
        </div>
      )}

      {/* 2/3, 1/3 dashboard grid */}
      <div className="dashboard-grid">
        {/* Left 2/3: Job Runs Table */}
        <div className="dashboard-section">
          <div className="section-header">
            Job Runs ({runs.length})
            <Link 
              to="/job-management"
              className="btn-icon btn-success"
              title="Create new job"
            >
              <Plus size={14} />
            </Link>
          </div>
          
          {/* Filter Bar */}
          <div className="filter-bar">
            <Filter size={14} className="filter-icon" />
            <span>Filter by Job:</span>
            <select
              className="filter-select"
              value={selectedJobId || ''}
              onChange={(e) => setSelectedJobId(e.target.value ? parseInt(e.target.value) : undefined)}
            >
              <option value="">All Jobs</option>
              {jobs.map(job => (
                <option key={job.id} value={job.id}>
                  {job.name}
                </option>
              ))}
            </select>
            {selectedJobId && (
              <button
                className="btn-icon btn-ghost"
                onClick={() => setSelectedJobId(undefined)}
                title="Clear filter"
              >
                <X size={14} />
              </button>
            )}
            <span style={{ marginLeft: 'auto', fontSize: '11px', color: 'var(--neutral-500)' }}>
              Showing: {getFilteredJobName()}
            </span>
          </div>
          
          <div className="compact-content">
            {runs.length === 0 ? (
              <div className="empty-state">
                <h3>No job runs found</h3>
                <p>{selectedJobId ? `No runs found for ${getFilteredJobName()}` : 'No job runs have been executed yet'}</p>
                <Link 
                  to="/job-management"
                  className="btn-icon btn-success"
                  title="Create first job"
                >
                  <Plus size={16} />
                </Link>
              </div>
            ) : (
              <div className="table-container">
                <table className="runs-table">
                  <thead>
                    <tr>
                      <th>Job</th>
                      <th>Status</th>
                      <th>Requested By</th>
                      <th>Started</th>
                      <th>Duration</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {runs.map((run) => (
                      <tr 
                        key={run.id} 
                        className={selectedRun?.id === run.id ? 'selected' : ''}
                        onClick={() => handleRunSelect(run)}
                      >
                        <td>
                          <div style={{ fontWeight: '500' }}>{getJobName(run.job_id)}</div>
                          <div style={{ fontSize: '10px', color: 'var(--neutral-500)' }}>Run #{run.id}</div>
                        </td>
                        <td>
                          <div className="run-status-icon">
                            {getRunStatusIcon(run.status)}
                            <span className={`status-badge ${getRunStatusBadge(run.status)}`}>
                              {run.status}
                            </span>
                          </div>
                        </td>
                        <td style={{ fontSize: '11px', color: 'var(--neutral-600)' }}>
                          User {run.requested_by}
                        </td>
                        <td style={{ fontSize: '11px', color: 'var(--neutral-500)' }}>
                          {run.started_at ? new Date(run.started_at).toLocaleString() : 'Not started'}
                        </td>
                        <td style={{ fontSize: '11px', color: 'var(--neutral-500)' }}>
                          {formatDuration(run.started_at, run.finished_at)}
                        </td>
                        <td>
                          <button 
                            className="btn-icon btn-ghost"
                            onClick={(e) => {
                              e.stopPropagation();
                              navigate(`/job-runs/${run.id}`);
                            }}
                            title="View full details"
                          >
                            <ExternalLink size={14} />
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

        {/* Right 1/3: Run Details Panel */}
        <div className="dashboard-section">
          <div className="section-header">
            {selectedRun ? `Run #${selectedRun.id} Details` : 'Select Run'}
          </div>
          <div className="compact-content">
            {selectedRun ? (
              <div className="details-panel">
                <h3>Run #{selectedRun.id}</h3>
                
                <div className="detail-group">
                  <div className="detail-label">Job</div>
                  <div className="detail-value">{getJobName(selectedRun.job_id)}</div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">Status</div>
                  <div className="detail-value">
                    <div className="run-status-icon">
                      {getRunStatusIcon(selectedRun.status)}
                      <span className={`status-badge ${getRunStatusBadge(selectedRun.status)}`}>
                        {selectedRun.status}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">Requested By</div>
                  <div className="detail-value">User {selectedRun.requested_by}</div>
                </div>

                {selectedRun.correlation_id && (
                  <div className="detail-group">
                    <div className="detail-label">Correlation ID</div>
                    <div className="detail-value" style={{ fontFamily: 'monospace', fontSize: '11px' }}>
                      {selectedRun.correlation_id}
                    </div>
                  </div>
                )}

                <div className="detail-group">
                  <div className="detail-label">Queued</div>
                  <div className="detail-value">{new Date(selectedRun.queued_at).toLocaleString()}</div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">Started</div>
                  <div className="detail-value">
                    {selectedRun.started_at ? new Date(selectedRun.started_at).toLocaleString() : 'Not started'}
                  </div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">Finished</div>
                  <div className="detail-value">
                    {selectedRun.finished_at ? new Date(selectedRun.finished_at).toLocaleString() : 'Not finished'}
                  </div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">Duration</div>
                  <div className="detail-value">
                    {formatDuration(selectedRun.started_at, selectedRun.finished_at)}
                  </div>
                </div>

                {selectedRun.parameters && Object.keys(selectedRun.parameters).length > 0 && (
                  <div className="detail-group">
                    <div className="detail-label">Parameters</div>
                    <div className="detail-value">
                      <div className="parameters-json">
                        {JSON.stringify(selectedRun.parameters, null, 2)}
                      </div>
                    </div>
                  </div>
                )}

                {/* Steps Section */}
                <div className="steps-section">
                  <div className="detail-label">Steps ({runSteps.length})</div>
                  {loadingSteps ? (
                    <div style={{ textAlign: 'center', padding: '20px', color: 'var(--neutral-500)' }}>
                      Loading steps...
                    </div>
                  ) : runSteps.length === 0 ? (
                    <div style={{ textAlign: 'center', padding: '20px', color: 'var(--neutral-500)' }}>
                      No steps found
                    </div>
                  ) : (
                    <div>
                      {runSteps.map((step, index) => (
                        <div key={step.id} className="step-item">
                          <div className="step-header">
                            <div className="step-title">
                              Step {step.idx + 1}: {step.type}
                            </div>
                            <div className="run-status-icon">
                              {getRunStatusIcon(step.status)}
                              <span className={`status-badge ${getRunStatusBadge(step.status)}`}>
                                {step.status}
                              </span>
                            </div>
                          </div>
                          <div className="step-details">
                            {step.target_id && <div>Target: {step.target_id}</div>}
                            {step.shell && <div>Shell: {step.shell}</div>}
                            {step.exit_code !== null && step.exit_code !== undefined && (
                              <div>Exit Code: {step.exit_code}</div>
                            )}
                            {step.started_at && (
                              <div>Duration: {formatDuration(step.started_at, step.finished_at)}</div>
                            )}
                          </div>
                          {step.stdout && (
                            <div className="step-output">
                              {step.stdout.substring(0, 200)}{step.stdout.length > 200 ? '...' : ''}
                            </div>
                          )}
                          {step.stderr && (
                            <div className="step-output step-error">
                              {step.stderr.substring(0, 200)}{step.stderr.length > 200 ? '...' : ''}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div className="action-buttons">
                  <button 
                    className="btn-primary"
                    onClick={() => navigate(`/job-runs/${selectedRun.id}`)}
                  >
                    View Full Details
                  </button>
                </div>
              </div>
            ) : (
              <div className="empty-state">
                <p>Select a job run to view details and execution steps</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default JobRuns;