import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { jobRunApi, jobApi, userApi, targetApi } from '../services/api';
import { JobRun, JobRunStep, Job, User, Target } from '../types';
import { Play, CheckCircle, XCircle, Clock, AlertCircle, Pause, Filter, X, Minus, ExternalLink, Maximize2, Upload } from 'lucide-react';

// Component to check if Celery task exists and render appropriate link
const CeleryTaskLink: React.FC<{ jobRunId: number; correlationId: string }> = ({ jobRunId, correlationId }) => {
  const [taskExists, setTaskExists] = useState<boolean | null>(null);
  const [checking, setChecking] = useState(true);
  
  const taskId = `job_run_${jobRunId}_${correlationId}`;
  
  useEffect(() => {
    const checkTaskExists = async () => {
      try {
        // Check if task exists in Flower/Celery
        const response = await fetch(`/flower/api/task/info/${taskId}`);
        setTaskExists(response.ok);
      } catch (error) {
        console.log('Could not check task existence:', error);
        setTaskExists(false);
      } finally {
        setChecking(false);
      }
    };
    
    checkTaskExists();
  }, [taskId]);
  
  if (checking) {
    return (
      <span style={{ color: 'var(--neutral-500)' }}>
        {correlationId} <span style={{ opacity: 0.7 }}>(checking...)</span>
      </span>
    );
  }
  
  if (taskExists) {
    return (
      <a 
        href={`/history/celery-workers-iframe?task=${taskId}`}
        target="_blank"
        rel="noopener noreferrer"
        style={{ 
          color: 'var(--primary)', 
          textDecoration: 'none',
          borderBottom: '1px dotted var(--primary)',
          display: 'inline-flex',
          alignItems: 'center',
          gap: '4px'
        }}
        title="View task in Celery monitoring"
      >
        {correlationId}
        <ExternalLink size={12} />
      </a>
    );
  } else {
    return (
      <span 
        style={{ 
          color: 'var(--neutral-600)',
          display: 'inline-flex',
          alignItems: 'center',
          gap: '4px'
        }}
        title="Task no longer available in Celery (expired or deleted)"
      >
        {correlationId}
        <span style={{ fontSize: '12px', opacity: 0.7 }}>(expired)</span>
      </span>
    );
  }
};

const JobRuns: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [runs, setRuns] = useState<JobRun[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [targets, setTargets] = useState<Target[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedJobId, setSelectedJobId] = useState<number | undefined>(undefined);
  const [selectedRunId, setSelectedRunId] = useState<number | undefined>(undefined);
  const [selectedRun, setSelectedRun] = useState<JobRun | null>(null);
  const [runSteps, setRunSteps] = useState<JobRunStep[]>([]);
  const [loadingSteps, setLoadingSteps] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Pagination state for infinite scroll
  const [currentPage, setCurrentPage] = useState(0);
  const [hasMoreRuns, setHasMoreRuns] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [totalLoadedRuns, setTotalLoadedRuns] = useState(0);
  const [maxRunsReached, setMaxRunsReached] = useState(false);
  
  // Modal state for viewing full output
  const [outputModalOpen, setOutputModalOpen] = useState(false);
  const [modalOutputData, setModalOutputData] = useState<{
    stepName: string;
    stdout?: string;
    stderr?: string;
    exitCode?: number;
  } | null>(null);

  // Parse job_id and run_id from URL parameters on mount
  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    const jobIdParam = searchParams.get('job_id');
    const runIdParam = searchParams.get('run_id');
    
    if (jobIdParam) {
      const jobId = parseInt(jobIdParam, 10);
      if (!isNaN(jobId)) {
        setSelectedJobId(jobId);
      }
    }
    
    if (runIdParam) {
      const runId = parseInt(runIdParam, 10);
      if (!isNaN(runId)) {
        // We'll select the run after runs are loaded
        setSelectedRunId(runId);
      }
    }
  }, [location.search]);

  // Define fetch functions before they are used in useEffect
  const fetchJobs = useCallback(async () => {
    try {
      const response = await jobApi.list(0, 100);
      setJobs(response.jobs || []);
    } catch (error: any) {
      console.error('Failed to fetch jobs:', error);
    }
  }, []);

  const fetchUsers = useCallback(async () => {
    try {
      const response = await userApi.list(0, 100); // Get all users
      setUsers(response.data || []);
    } catch (error: any) {
      console.error('Failed to fetch users:', error);
    }
  }, []);

  const fetchTargets = useCallback(async () => {
    try {
      const response = await targetApi.list(0, 100); // Get all targets
      setTargets(response.targets || []);
    } catch (error: any) {
      console.error('Failed to fetch targets:', error);
    }
  }, []);

  const fetchRuns = useCallback(async (reset: boolean = true) => {
    try {
      if (reset) {
        setLoading(true);
        setCurrentPage(0);
        setHasMoreRuns(true);
        setMaxRunsReached(false);
        setTotalLoadedRuns(0);
      }
      
      const pageSize = reset ? 50 : 25; // Initial load: 50, subsequent: 25
      
      // Use functional update to get current totalLoadedRuns
      let currentTotalLoaded = 0;
      setTotalLoadedRuns(prev => {
        currentTotalLoaded = prev;
        return prev;
      });
      
      const skip = reset ? 0 : currentTotalLoaded;
      
      const response = await jobRunApi.list(skip, pageSize, selectedJobId);
      const newRuns = response.executions || [];
      
      if (reset) {
        setRuns(newRuns);
        setTotalLoadedRuns(newRuns.length);
        currentTotalLoaded = newRuns.length;
      } else {
        setRuns(prevRuns => [...prevRuns, ...newRuns]);
        setTotalLoadedRuns(prev => {
          const newTotal = prev + newRuns.length;
          currentTotalLoaded = newTotal;
          return newTotal;
        });
      }
      
      // Update pagination state
      const hasMore = newRuns.length === pageSize && currentTotalLoaded < (response.total || 0) && currentTotalLoaded < 500;
      setHasMoreRuns(hasMore);
      
      // Check if we've reached the 500 item limit
      if (currentTotalLoaded >= 500) {
        setMaxRunsReached(true);
        setHasMoreRuns(false);
      }
      
    } catch (error: any) {
      console.error('Failed to fetch job runs:', error);
      console.error('Error stack:', error.stack);
      setError(error.message || 'Failed to load job runs');
    } finally {
      setLoading(false);
    }
  }, [selectedJobId]);

  useEffect(() => {
    fetchRuns();
    fetchJobs();
    fetchUsers();
    fetchTargets();
  }, [selectedJobId, fetchRuns, fetchJobs, fetchUsers, fetchTargets]);

  useEffect(() => {
    if (selectedRun) {
      fetchRunSteps(selectedRun.id);
    }
  }, [selectedRun]);

  // Auto-select run when runs are loaded and we have a selectedRunId from URL
  useEffect(() => {
    if (selectedRunId && runs.length > 0 && !selectedRun) {
      const runToSelect = runs.find(run => run.id === selectedRunId);
      if (runToSelect) {
        setSelectedRun(runToSelect);
        // Clear the selectedRunId so it doesn't interfere with manual selection
        setSelectedRunId(undefined);
      }
    }
  }, [runs, selectedRunId, selectedRun]);

  // Infinite scroll detection
  useEffect(() => {
    const handleScroll = () => {
      if (loadingMore || !hasMoreRuns || maxRunsReached) return;
      
      const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
      const windowHeight = window.innerHeight;
      const documentHeight = document.documentElement.scrollHeight;
      
      // Load more when user is within 200px of the bottom
      if (scrollTop + windowHeight >= documentHeight - 200) {
        loadMoreRuns();
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [loadingMore, hasMoreRuns, maxRunsReached]);

  const loadMoreRuns = async () => {
    if (loadingMore || !hasMoreRuns || maxRunsReached) return;
    
    try {
      setLoadingMore(true);
      await fetchRuns(false); // false = don't reset, append to existing
    } catch (error: any) {
      console.error('Failed to load more runs:', error);
    } finally {
      setLoadingMore(false);
    }
  };

  const resetAndLoadRuns = () => {
    // Reset all pagination state and reload from beginning
    setRuns([]);
    setCurrentPage(0);
    setHasMoreRuns(true);
    setMaxRunsReached(false);
    setTotalLoadedRuns(0);
    fetchRuns(true);
  };



  const fetchRunSteps = async (runId: number) => {
    try {
      setLoadingSteps(true);
      const response = await jobRunApi.getSteps(runId);
      // Ensure response is always an array
      setRunSteps(Array.isArray(response) ? response : []);
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

  const getUserName = (userId: number) => {
    const user = users.find(u => u.id === userId);
    return user ? user.username : `User ${userId}`;
  };

  const getTargetInfo = (targetId: number) => {
    const target = targets.find(t => t.id === targetId);
    if (target) {
      return target.ip_address || target.hostname;
    }
    return `Target ${targetId}`;
  };

  const getStepCommand = (step: JobRunStep) => {
    if (!selectedRun) return step.step_id || 'Unknown';
    
    const job = jobs.find(j => j.id === selectedRun.job_id);
    if (!job || !job.workflow_definition || !job.workflow_definition.steps) {
      return step.step_id || 'Unknown';
    }
    
    // Find the step in the job definition by index
    const jobStep = job.workflow_definition.steps[step.execution_order];
    if (jobStep && jobStep.command) {
      return jobStep.command;
    }
    
    return step.step_id || 'Unknown';
  };

  const hasStatusInconsistency = () => {
    if (!selectedRun || !Array.isArray(runSteps) || runSteps.length === 0) return false;
    
    const jobStatus = selectedRun.status;
    const activeSteps = runSteps.filter(step => step.status !== 'skipped');
    
    // Type 1: Job complete but steps still queued/running
    const hasIncompleteSteps = activeSteps.some(step => 
      step.status === 'queued' || step.status === 'running'
    );
    
    // Type 2: Job failed but no steps actually failed
    const hasFailedSteps = activeSteps.some(step => step.status === 'failed');
    const jobFailedButNoFailedSteps = jobStatus === 'failed' && !hasFailedSteps && activeSteps.length > 0;
    
    // Type 3: Job succeeded but has failed steps
    const jobSucceededButHasFailedSteps = jobStatus === 'succeeded' && hasFailedSteps;
    
    return (
      ((jobStatus === 'succeeded' || jobStatus === 'failed') && hasIncompleteSteps) ||
      jobFailedButNoFailedSteps ||
      jobSucceededButHasFailedSteps
    );
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
      case 'skipped':
        return 'status-badge-neutral';
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
      case 'skipped':
        return <Minus size={14} />;
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

  const openOutputModal = (step: JobRunStep) => {
    setModalOutputData({
      stepName: `Step ${step.execution_order + 1}: ${step.step_type}`,
      stdout: JSON.stringify(step.output_data, null, 2),
      stderr: step.error_message || '',
      exitCode: undefined
    });
    setOutputModalOpen(true);
  };

  const closeOutputModal = () => {
    setOutputModalOpen(false);
    setModalOutputData(null);
  };

  const formatOutput = (output: string) => {
    // Replace \r\n and \n with actual line breaks, and handle other escape sequences
    return output
      .replace(/\\r\\n/g, '\n')
      .replace(/\\n/g, '\n')
      .replace(/\\r/g, '\n')
      .replace(/\r\n/g, '\n')
      .replace(/\r/g, '\n');
  };

  const exportOutput = (step: JobRunStep) => {
    const stepName = `Step_${step.execution_order + 1}_${step.step_type}`;
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `${stepName}_${timestamp}.txt`;
    
    let content = `=== ${stepName} Output ===\n`;
    content += `Job Run ID: ${step.job_execution_id}\n`;
    content += `Step Index: ${step.execution_order + 1}\n`;
    content += `Step Type: ${step.step_type}\n`;
    content += `Status: ${step.status}\n`;
    content += `Started: ${step.started_at ?? 'N/A'}\n`;
    content += `Finished: ${step.completed_at ?? 'N/A'}\n`;
    content += `\n${'='.repeat(50)}\n\n`;
    
    if (step.output_data && Object.keys(step.output_data).length > 0) {
      content += `OUTPUT DATA:\n`;
      content += `${'-'.repeat(20)}\n`;
      content += `${JSON.stringify(step.output_data, null, 2)}\n\n`;
    }
    
    if (step.error_message) {
      content += `ERROR MESSAGE:\n`;
      content += `${'-'.repeat(20)}\n`;
      content += `${step.error_message}\n\n`;
    }
    
    if (!step.output_data || Object.keys(step.output_data).length === 0) {
      if (!step.error_message) {
        content += `No output available.\n`;
      }
    }
    
    // Create and download file
    const blob = new Blob([content], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
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
              {getFilteredJobName()} • {totalLoadedRuns} loaded{hasMoreRuns ? ' (scroll for more)' : ''}
            </span>
          </div>
          
          <div className="compact-content">
            {runs.length === 0 ? (
              <div className="empty-state">
                <h3>No job runs found</h3>
                <p>{selectedJobId ? `No runs found for ${getFilteredJobName()}` : 'No job runs have been executed yet'}</p>
              </div>
            ) : (
              <div className="table-container">
                <table className="runs-table">
                  <thead>
                    <tr>
                      <th>Run #</th>
                      <th>Job</th>
                      <th>Status</th>
                      <th>Requested By</th>
                      <th>Started</th>
                      <th>Duration</th>
                    </tr>
                  </thead>
                  <tbody>
                    {runs.map((run) => (
                      <tr 
                        key={run.id} 
                        className={selectedRun?.id === run.id ? 'selected' : ''}
                        onClick={() => handleRunSelect(run)}
                      >
                        <td style={{ fontSize: '11px', color: 'var(--neutral-600)', textAlign: 'center' }}>
                          {run.id}
                        </td>
                        <td>
                          <div style={{ fontWeight: '500' }}>{getJobName(run.job_id)}</div>
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
                          {run.started_by ? getUserName(run.started_by) : 'System'}
                        </td>
                        <td style={{ fontSize: '11px', color: 'var(--neutral-500)' }}>
                          {run.started_at ? new Date(run.started_at).toLocaleString() : 'Not started'}
                        </td>
                        <td style={{ fontSize: '11px', color: 'var(--neutral-500)' }}>
                          {formatDuration(run.started_at, run.completed_at)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                
                {/* Loading and pagination controls */}
                {loadingMore && (
                  <div style={{ 
                    textAlign: 'center', 
                    padding: '20px', 
                    color: 'var(--neutral-500)',
                    fontSize: '14px'
                  }}>
                    Loading more runs...
                  </div>
                )}
                
                {maxRunsReached && (
                  <div style={{ 
                    textAlign: 'center', 
                    padding: '20px',
                    borderTop: '1px solid var(--neutral-200)'
                  }}>
                    <div style={{ 
                      color: 'var(--neutral-600)', 
                      fontSize: '14px', 
                      marginBottom: '12px' 
                    }}>
                      Showing {totalLoadedRuns} most recent runs (limit reached)
                    </div>
                    <button
                      onClick={resetAndLoadRuns}
                      style={{
                        background: 'var(--primary)',
                        color: 'white',
                        border: 'none',
                        padding: '8px 16px',
                        borderRadius: '4px',
                        fontSize: '12px',
                        cursor: 'pointer'
                      }}
                    >
                      Load Older Runs
                    </button>
                  </div>
                )}
                
                {!hasMoreRuns && !maxRunsReached && totalLoadedRuns > 0 && (
                  <div style={{ 
                    textAlign: 'center', 
                    padding: '20px', 
                    color: 'var(--neutral-500)',
                    fontSize: '12px',
                    borderTop: '1px solid var(--neutral-200)'
                  }}>
                    All runs loaded ({totalLoadedRuns} total)
                  </div>
                )}
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
                {/* 3-column grid for run details */}
                <div className="detail-grid-3col">
                    <div className="detail-item">
                      <label>Job</label>
                      <div className="detail-value">{getJobName(selectedRun.job_id)}</div>
                    </div>

                    <div className="detail-item">
                      <label>Status</label>
                      <div className="detail-value">
                        <div className="run-status-icon">
                          {getRunStatusIcon(selectedRun.status)}
                          <span className={`status-badge ${getRunStatusBadge(selectedRun.status)}`}>
                            {selectedRun.status}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="detail-item">
                      <label>Started By</label>
                      <div className="detail-value">{selectedRun.started_by ? getUserName(selectedRun.started_by) : 'System'}</div>
                    </div>

                    <div className="detail-item">
                      <label>Created</label>
                      <div className="detail-value">{new Date(selectedRun.created_at).toLocaleString()}</div>
                    </div>

                    <div className="detail-item">
                      <label>Started</label>
                      <div className="detail-value">
                        {selectedRun.started_at ? new Date(selectedRun.started_at).toLocaleString() : 'Not started'}
                      </div>
                    </div>

                    <div className="detail-item">
                      <label>Duration</label>
                      <div className="detail-value">
                        {formatDuration(selectedRun.started_at, selectedRun.completed_at)}
                      </div>
                    </div>

                    {selectedRun.completed_at && (
                      <div className="detail-item">
                        <label>Completed</label>
                        <div className="detail-value">
                          {new Date(selectedRun.completed_at).toLocaleString()}
                        </div>
                      </div>
                    )}

                    {selectedRun.execution_id && (
                      <div className="detail-item detail-item-span-2-3">
                        <label>Execution ID</label>
                        <div className="detail-value">
                          <CeleryTaskLink 
                            jobRunId={selectedRun.id} 
                            correlationId={selectedRun.execution_id} 
                          />
                        </div>
                      </div>
                    )}
                  </div>

                {selectedRun.input_data && Object.keys(selectedRun.input_data).length > 0 && (
                  <div className="detail-section">
                    <div className="detail-section-title">Input Data</div>
                    <div className="detail-value">
                      <div className="parameters-json">
                        {JSON.stringify(selectedRun.input_data, null, 2)}
                      </div>
                    </div>
                  </div>
                )}

                {/* Steps Section */}
                <div className="detail-section">
                  <div className="detail-section-title">Steps ({Array.isArray(runSteps) ? runSteps.length : 0})</div>
                  {hasStatusInconsistency() && (
                    <div style={{ 
                      background: 'var(--warning-light)', 
                      border: '1px solid var(--warning)', 
                      borderRadius: '4px', 
                      padding: '8px 12px', 
                      marginBottom: '12px',
                      fontSize: '12px',
                      color: 'var(--warning-dark)'
                    }}>
                      ⚠️ Status inconsistency detected: Job status "{selectedRun?.status}" doesn't match step statuses. This indicates a backend processing issue.
                    </div>
                  )}
                  {loadingSteps ? (
                    <div style={{ textAlign: 'center', padding: '20px', color: 'var(--neutral-500)' }}>
                      Loading steps...
                    </div>
                  ) : !Array.isArray(runSteps) || runSteps.length === 0 ? (
                    <div style={{ textAlign: 'center', padding: '20px', color: 'var(--neutral-500)' }}>
                      No steps found
                    </div>
                  ) : (
                    <div>
                      {runSteps.map((step, index) => (
                        <div key={step.id} style={{ marginBottom: '16px', paddingBottom: '16px', borderBottom: index < runSteps.length - 1 ? '1px solid var(--neutral-200)' : 'none' }}>
                          {/* 3-column grid for step details */}
                          <div className="detail-grid-3col">
                            {/* Row 1: Step, Status, Target */}
                            <div className="detail-item">
                              <label>Step {step.execution_order + 1}</label>
                              <div className="detail-value">{step.step_type}</div>
                            </div>
                            
                            <div className="detail-item">
                              <label>Status</label>
                              <div className="detail-value">
                                <div className="run-status-icon">
                                  {getRunStatusIcon(step.status)}
                                  <span className={`status-badge ${getRunStatusBadge(step.status)}`}>
                                    {step.status}
                                  </span>
                                </div>
                              </div>
                            </div>
                            
                            <div className="detail-item">
                              <label>Step Name</label>
                              <div className="detail-value">{step.step_name}</div>
                            </div>
                            
                            {/* Row 2: Command (spans all columns) */}
                            <div className="detail-item detail-item-span-remaining">
                              <label>Command</label>
                              <div className="detail-value">{getStepCommand(step)}</div>
                            </div>
                            
                            {/* Row 3: Output (spans all columns) */}
                            {((step.output_data && Object.keys(step.output_data).length > 0) || step.error_message) && (
                              <div className="detail-item detail-item-span-remaining">
                                <label style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                  <span>Output</span>
                                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                                    <button
                                      onClick={() => exportOutput(step)}
                                      style={{
                                        background: 'none',
                                        border: 'none',
                                        cursor: 'pointer',
                                        color: 'var(--primary)',
                                        padding: '2px',
                                        borderRadius: '3px',
                                        display: 'flex',
                                        alignItems: 'center',
                                        transition: 'background-color 0.2s'
                                      }}
                                      onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--neutral-100)'}
                                      onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                                      title="Export output to file"
                                    >
                                      <Upload size={14} />
                                    </button>
                                    <button
                                      onClick={() => openOutputModal(step)}
                                      style={{
                                        background: 'none',
                                        border: 'none',
                                        cursor: 'pointer',
                                        color: 'var(--primary)',
                                        padding: '2px',
                                        borderRadius: '3px',
                                        display: 'flex',
                                        alignItems: 'center',
                                        transition: 'background-color 0.2s'
                                      }}
                                      onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--neutral-100)'}
                                      onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                                      title="View full output"
                                    >
                                      <Maximize2 size={14} />
                                    </button>
                                  </div>
                                </label>
                                <div className="detail-value">
                                  {step.output_data && Object.keys(step.output_data).length > 0 && (
                                    <div>{JSON.stringify(step.output_data).substring(0, 200)}{JSON.stringify(step.output_data).length > 200 ? '...' : ''}</div>
                                  )}
                                  {step.error_message && (
                                    <div style={{ color: 'var(--error)' }}>
                                      Error: {step.error_message.substring(0, 200)}{step.error_message.length > 200 ? '...' : ''}
                                    </div>
                                  )}
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
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

      {/* Output Modal */}
      {outputModalOpen && modalOutputData && (
        <div 
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000
          }}
          onClick={closeOutputModal}
        >
          <div 
            style={{
              backgroundColor: 'white',
              borderRadius: '8px',
              width: '90%',
              maxWidth: '800px',
              maxHeight: '80%',
              display: 'flex',
              flexDirection: 'column',
              boxShadow: '0 10px 25px rgba(0, 0, 0, 0.2)'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div style={{
              padding: '16px 20px',
              borderBottom: '1px solid var(--neutral-200)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 600 }}>
                {modalOutputData.stepName} - Output
              </h3>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <button
                  onClick={() => {
                    // Find the step data for export
                    const step = Array.isArray(runSteps) ? runSteps.find(s => 
                      `Step ${s.execution_order + 1}: ${s.step_type}` === modalOutputData.stepName
                    ) : null;
                    if (step) exportOutput(step);
                  }}
                  style={{
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    color: 'var(--primary)',
                    padding: '4px',
                    borderRadius: '4px',
                    display: 'flex',
                    alignItems: 'center'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--neutral-100)'}
                  onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                  title="Export output to file"
                >
                  <Upload size={18} />
                </button>
                <button
                  onClick={closeOutputModal}
                  style={{
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    color: 'var(--neutral-600)',
                    padding: '4px',
                    borderRadius: '4px',
                    display: 'flex',
                    alignItems: 'center'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--neutral-100)'}
                  onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                  title="Close modal"
                >
                  <X size={20} />
                </button>
              </div>
            </div>

            {/* Modal Content */}
            <div style={{
              padding: '20px',
              overflow: 'auto',
              flex: 1
            }}>
              {modalOutputData.stdout && (
                <div style={{ marginBottom: '16px' }}>
                  <h4 style={{ 
                    margin: '0 0 8px 0', 
                    fontSize: '14px', 
                    fontWeight: 600,
                    color: 'var(--neutral-700)'
                  }}>
                    Standard Output:
                  </h4>
                  <pre style={{
                    backgroundColor: 'var(--neutral-50)',
                    border: '1px solid var(--neutral-200)',
                    borderRadius: '4px',
                    padding: '12px',
                    margin: 0,
                    fontSize: '13px',
                    fontFamily: 'Monaco, Consolas, "Courier New", monospace',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                    maxHeight: '300px',
                    overflow: 'auto'
                  }}>
                    {formatOutput(modalOutputData.stdout)}
                  </pre>
                </div>
              )}

              {modalOutputData.stderr && (
                <div style={{ marginBottom: '16px' }}>
                  <h4 style={{ 
                    margin: '0 0 8px 0', 
                    fontSize: '14px', 
                    fontWeight: 600,
                    color: 'var(--error)'
                  }}>
                    Standard Error:
                  </h4>
                  <pre style={{
                    backgroundColor: '#fef2f2',
                    border: '1px solid #fecaca',
                    borderRadius: '4px',
                    padding: '12px',
                    margin: 0,
                    fontSize: '13px',
                    fontFamily: 'Monaco, Consolas, "Courier New", monospace',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                    maxHeight: '300px',
                    overflow: 'auto',
                    color: 'var(--error)'
                  }}>
                    {formatOutput(modalOutputData.stderr)}
                  </pre>
                </div>
              )}

              {modalOutputData.exitCode !== undefined && (
                <div>
                  <h4 style={{ 
                    margin: '0 0 8px 0', 
                    fontSize: '14px', 
                    fontWeight: 600,
                    color: 'var(--neutral-700)'
                  }}>
                    Exit Code:
                  </h4>
                  <span style={{
                    display: 'inline-block',
                    backgroundColor: modalOutputData.exitCode === 0 ? 'var(--success-light)' : 'var(--error-light)',
                    color: modalOutputData.exitCode === 0 ? 'var(--success)' : 'var(--error)',
                    padding: '4px 8px',
                    borderRadius: '4px',
                    fontSize: '13px',
                    fontWeight: 600
                  }}>
                    {modalOutputData.exitCode}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default JobRuns;