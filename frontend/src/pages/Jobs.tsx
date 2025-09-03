import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Job, JobRun } from '../types';
import { jobApi, jobRunApi } from '../services/api';
import VisualJobBuilder from '../components/VisualJobBuilder';
import { Plus, Play, Edit, Trash2, Clock, CheckCircle, XCircle, AlertCircle, Pause } from 'lucide-react';

const Jobs: React.FC = () => {
  const navigate = useNavigate();
  const { action, id } = useParams<{ action?: string; id?: string }>();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [jobRuns, setJobRuns] = useState<JobRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [selectedJobRun, setSelectedJobRun] = useState<JobRun | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isEditing = action === 'edit' && id;
  const isCreating = action === 'create';

  useEffect(() => {
    fetchJobs();
    fetchJobRuns();
  }, []);

  useEffect(() => {
    if (isEditing && id) {
      const job = jobs.find(j => j.id === parseInt(id));
      if (job) {
        setSelectedJob(job);
        setShowCreateForm(true);
      }
    } else if (isCreating) {
      setSelectedJob(null);
      setShowCreateForm(true);
    }
  }, [isEditing, isCreating, id, jobs]);

  const fetchJobs = async () => {
    try {
      setLoading(true);
      const response = await jobApi.list();
      setJobs(response.jobs || []);
    } catch (error: any) {
      console.error('Failed to fetch jobs:', error);
      setError(error.message || 'Failed to load jobs');
      setJobs([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchJobRuns = async (jobId?: number) => {
    try {
      const response = await jobRunApi.list(0, 100, jobId);
      setJobRuns(response.runs || []);
    } catch (error: any) {
      console.error('Failed to fetch job runs:', error);
      setJobRuns([]);
    }
  };

  const handleDelete = async (jobId: number) => {
    if (window.confirm('Delete this job? This action cannot be undone.')) {
      try {
        await jobApi.delete(jobId);
        fetchJobs();
        if (selectedJob?.id === jobId) {
          setSelectedJob(null);
        }
      } catch (error: any) {
        console.error('Failed to delete job:', error);
        setError(error.message || 'Failed to delete job');
      }
    }
  };

  const handleRunJob = async (jobId: number) => {
    try {
      await jobApi.run(jobId);
      alert('Job started successfully!');
      fetchJobRuns(); // Refresh job runs
    } catch (error: any) {
      console.error('Failed to run job:', error);
      alert('Failed to start job. Check the logs for details.');
    }
  };

  const handleJobSaved = () => {
    fetchJobs();
    setShowCreateForm(false);
    navigate('/job-management');
  };

  const handleJobSelect = (job: Job) => {
    setSelectedJob(job);
    setSelectedJobRun(null);
    fetchJobRuns(job.id); // Load runs for this specific job
  };

  const getJobStatusBadge = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'active':
      case 'enabled':
        return 'status-badge-success';
      case 'inactive':
      case 'disabled':
        return 'status-badge-neutral';
      case 'error':
        return 'status-badge-danger';
      default:
        return 'status-badge-info';
    }
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
        return <Pause size={14} />;
      default:
        return <AlertCircle size={14} />;
    }
  };

  const formatDuration = (started: string | undefined, finished?: string | undefined) => {
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

  const getJobName = (jobId: number) => {
    const job = jobs.find(j => j.id === jobId);
    return job ? job.name : `Job ${jobId}`;
  };

  if (loading && jobs.length === 0) {
    return (
      <div className="loading-overlay">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  // If showing the form, render it full-screen
  if (showCreateForm) {
    return (
      <div className="main-content">
        <div className="page-header">
          <h1 className="page-title">
            {isEditing ? 'Edit Job' : 'Create Job'}
          </h1>
          <div className="page-actions">
            <button 
              type="button" 
              className="btn btn-ghost"
              onClick={() => {
                setShowCreateForm(false);
                navigate('/job-management');
              }}
            >
              Cancel
            </button>
          </div>
        </div>

        <div style={{ marginTop: 'var(--space-4)' }}>
          <VisualJobBuilder
            editingJob={selectedJob}
            onJobCreate={handleJobSaved}
            onCancel={() => {
              setShowCreateForm(false);
              navigate('/job-management');
            }}
          />
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
            grid-template-columns: 1fr 1fr 1fr;
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
          
          /* Jobs table styles */
          .jobs-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
          }
          .jobs-table th {
            background: var(--neutral-50);
            padding: 6px 8px;
            text-align: left;
            font-weight: 600;
            color: var(--neutral-700);
            border-bottom: 1px solid var(--neutral-200);
            font-size: 11px;
          }
          .jobs-table td {
            padding: 6px 8px;
            border-bottom: 1px solid var(--neutral-100);
            vertical-align: middle;
            font-size: 12px;
          }
          .jobs-table tr:hover {
            background: var(--neutral-50);
          }
          .jobs-table tr.selected {
            background: var(--primary-blue-light);
            border-left: 3px solid var(--primary-blue);
          }
          .jobs-table tr {
            cursor: pointer;
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
          
          .job-steps-count {
            font-size: 10px;
            color: var(--neutral-500);
          }
          
          .run-targets-count {
            font-size: 10px;
            color: var(--neutral-500);
          }
        `}
      </style>
      
      {/* Dashboard-style header */}
      <div className="dashboard-header">
        <div className="header-left">
          <h1>Job Management</h1>
          <p className="header-subtitle">Create, manage, and monitor automated job executions</p>
        </div>
        <div className="header-actions">
          <button 
            className="btn-icon btn-success"
            onClick={() => {
              setShowCreateForm(true);
              navigate('/job-management/create');
            }}
            title="Create new job"
          >
            <Plus size={16} />
          </button>
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

      {/* 3-column dashboard grid */}
      <div className="dashboard-grid">
        {/* Column 1: Jobs */}
        <div className="dashboard-section">
          <div className="section-header">
            Jobs ({jobs.length})
            <button 
              className="btn-icon btn-success"
              onClick={() => {
                setShowCreateForm(true);
                navigate('/job-management/create');
              }}
              title="Create new job"
            >
              <Plus size={14} />
            </button>
          </div>
          <div className="compact-content">
            {jobs.length === 0 ? (
              <div className="empty-state">
                <h3>No jobs found</h3>
                <p>Create your first job to automate tasks on your targets.</p>
                <button 
                  className="btn-icon btn-success"
                  onClick={() => {
                    setShowCreateForm(true);
                    navigate('/job-management/create');
                  }}
                  title="Create first job"
                >
                  <Plus size={16} />
                </button>
              </div>
            ) : (
              <div className="table-container">
                <table className="jobs-table">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Status</th>
                      <th>Created</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {jobs.map((job) => (
                      <tr 
                        key={job.id} 
                        className={selectedJob?.id === job.id ? 'selected' : ''}
                        onClick={() => handleJobSelect(job)}
                      >
                        <td>
                          <div style={{ fontWeight: '500' }}>{job.name}</div>
                          <div className="job-steps-count">ID: {job.id}</div>
                        </td>
                        <td>
                          <span className={`status-badge ${getJobStatusBadge('active')}`}>
                            Active
                          </span>
                        </td>
                        <td style={{ fontSize: '11px', color: 'var(--neutral-500)' }}>
                          {new Date(job.created_at).toLocaleDateString()}
                        </td>
                        <td>
                          <div style={{ display: 'flex', gap: '2px' }}>
                            <button 
                              className="btn-icon btn-success"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleRunJob(job.id);
                              }}
                              title="Run job"
                            >
                              <Play size={14} />
                            </button>
                            <button 
                              className="btn-icon btn-ghost"
                              onClick={(e) => {
                                e.stopPropagation();
                                setSelectedJob(job);
                                setShowCreateForm(true);
                                navigate(`/job-management/edit/${job.id}`);
                              }}
                              title="Edit job"
                            >
                              <Edit size={14} />
                            </button>
                            <button 
                              className="btn-icon btn-danger"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDelete(job.id);
                              }}
                              title="Delete job"
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

        {/* Column 2: Job Runs */}
        <div className="dashboard-section">
          <div className="section-header">
            Job Runs ({jobRuns.length})
            {selectedJob && (
              <span style={{ fontSize: '11px', color: 'var(--neutral-500)' }}>
                for {selectedJob.name}
              </span>
            )}
          </div>
          <div className="compact-content">
            {jobRuns.length === 0 ? (
              <div className="empty-state">
                <h3>No job runs</h3>
                <p>{selectedJob ? `No runs found for ${selectedJob.name}` : 'Select a job to view its runs'}</p>
              </div>
            ) : (
              <div className="table-container">
                <table className="runs-table">
                  <thead>
                    <tr>
                      <th>Job</th>
                      <th>Status</th>
                      <th>Started</th>
                      <th>Duration</th>
                    </tr>
                  </thead>
                  <tbody>
                    {jobRuns.map((run) => (
                      <tr 
                        key={run.id} 
                        className={selectedJobRun?.id === run.id ? 'selected' : ''}
                        onClick={() => setSelectedJobRun(run)}
                      >
                        <td>
                          <div style={{ fontWeight: '500' }}>{getJobName(run.job_id)}</div>
                          <div className="run-targets-count">Run #{run.id}</div>
                        </td>
                        <td>
                          <div className="run-status-icon">
                            {getRunStatusIcon(run.status)}
                            <span className={`status-badge ${getRunStatusBadge(run.status)}`}>
                              {run.status}
                            </span>
                          </div>
                        </td>
                        <td style={{ fontSize: '11px', color: 'var(--neutral-500)' }}>
                          {run.started_at ? new Date(run.started_at).toLocaleString() : '-'}
                        </td>
                        <td style={{ fontSize: '11px', color: 'var(--neutral-500)' }}>
                          {formatDuration(run.started_at, run.finished_at)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Column 3: Details Panel */}
        <div className="dashboard-section">
          <div className="section-header">
            {selectedJobRun ? 'Run Details' : selectedJob ? 'Job Details' : 'Select Item'}
          </div>
          <div className="compact-content">
            {selectedJobRun ? (
              <div className="details-panel">
                <h3>Run #{selectedJobRun.id}</h3>
                
                <div className="detail-group">
                  <div className="detail-label">Job</div>
                  <div className="detail-value">{getJobName(selectedJobRun.job_id)}</div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">Status</div>
                  <div className="detail-value">
                    <div className="run-status-icon">
                      {getRunStatusIcon(selectedJobRun.status)}
                      <span className={`status-badge ${getRunStatusBadge(selectedJobRun.status)}`}>
                        {selectedJobRun.status}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">Started</div>
                  <div className="detail-value">
                    {selectedJobRun.started_at ? new Date(selectedJobRun.started_at).toLocaleString() : '-'}
                  </div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">Finished</div>
                  <div className="detail-value">
                    {selectedJobRun.finished_at ? new Date(selectedJobRun.finished_at).toLocaleString() : '-'}
                  </div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">Duration</div>
                  <div className="detail-value">
                    {formatDuration(selectedJobRun.started_at, selectedJobRun.finished_at)}
                  </div>
                </div>

                {selectedJobRun.status === 'failed' && (
                  <div className="detail-group">
                    <div className="detail-label">Status</div>
                    <div className="detail-value" style={{ color: 'var(--danger-red)', fontSize: '11px' }}>
                      Job execution failed
                    </div>
                  </div>
                )}

                <div className="action-buttons">
                  <button 
                    className="btn-primary"
                    onClick={() => navigate(`/job-runs/${selectedJobRun.id}`)}
                  >
                    View Details
                  </button>
                </div>
              </div>
            ) : selectedJob ? (
              <div className="details-panel">
                <h3>{selectedJob.name}</h3>
                
                <div className="detail-group">
                  <div className="detail-label">ID</div>
                  <div className="detail-value">{selectedJob.id}</div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">Status</div>
                  <div className="detail-value">
                    <span className={`status-badge ${getJobStatusBadge('active')}`}>
                      Active
                    </span>
                  </div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">Created</div>
                  <div className="detail-value">{new Date(selectedJob.created_at).toLocaleString()}</div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">Version</div>
                  <div className="detail-value">v{selectedJob.version}</div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">Recent Runs</div>
                  <div className="detail-value">
                    {jobRuns.filter(run => run.job_id === selectedJob.id).length} total runs
                  </div>
                </div>

                <div className="action-buttons">
                  <button 
                    className="btn-icon btn-success"
                    onClick={() => handleRunJob(selectedJob.id)}
                    title="Run job"
                  >
                    <Play size={16} />
                  </button>
                  <button 
                    className="btn-icon btn-ghost"
                    onClick={() => {
                      setShowCreateForm(true);
                      navigate(`/job-management/edit/${selectedJob.id}`);
                    }}
                    title="Edit job"
                  >
                    <Edit size={16} />
                  </button>
                  <button 
                    className="btn-icon btn-danger"
                    onClick={() => handleDelete(selectedJob.id)}
                    title="Delete job"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            ) : (
              <div className="empty-state">
                <p>Select a job or job run to view details</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Jobs;