import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { jobRunApi, jobApi } from '../services/api';
import { JobRun, Job } from '../types';

const JobRuns: React.FC = () => {
  const [runs, setRuns] = useState<JobRun[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedJobId, setSelectedJobId] = useState<number | undefined>(undefined);

  useEffect(() => {
    fetchRuns();
    fetchJobs();
  }, [selectedJobId]);

  const fetchRuns = async () => {
    try {
      const response = await jobRunApi.list(0, 100, selectedJobId);
      setRuns(response.runs);
    } catch (error) {
      console.error('Failed to fetch job runs:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchJobs = async () => {
    try {
      const response = await jobApi.list(0, 100, false); // Include inactive jobs
      setJobs(response.jobs);
    } catch (error) {
      console.error('Failed to fetch jobs:', error);
    }
  };

  const getJobName = (jobId: number) => {
    const job = jobs.find(j => j.id === jobId);
    return job ? job.name : `Job ${jobId}`;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'succeeded':
        return '#d4edda';
      case 'failed':
        return '#f8d7da';
      case 'running':
        return '#d1ecf1';
      case 'queued':
        return '#fff3cd';
      case 'canceled':
        return '#e2e3e5';
      default:
        return '#f8f9fa';
    }
  };

  const getStatusTextColor = (status: string) => {
    switch (status) {
      case 'succeeded':
        return '#155724';
      case 'failed':
        return '#721c24';
      case 'running':
        return '#0c5460';
      case 'queued':
        return '#856404';
      case 'canceled':
        return '#6c757d';
      default:
        return '#495057';
    }
  };

  const formatDuration = (started: string, finished?: string) => {
    if (!started) return '-';
    
    const startTime = new Date(started);
    const endTime = finished ? new Date(finished) : new Date();
    const durationMs = endTime.getTime() - startTime.getTime();
    
    const seconds = Math.floor(durationMs / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    } else {
      return `${seconds}s`;
    }
  };

  if (loading) return <div>Loading job runs...</div>;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h1>Job Runs</h1>
        <Link to="/jobs" className="btn btn-primary">
          Create New Job
        </Link>
      </div>

      {/* Filter by Job */}
      <div className="card" style={{ marginBottom: '20px' }}>
        <div className="form-group">
          <label>Filter by Job:</label>
          <select
            value={selectedJobId || ''}
            onChange={(e) => setSelectedJobId(e.target.value ? parseInt(e.target.value) : undefined)}
            style={{ width: '300px' }}
          >
            <option value="">All Jobs</option>
            {jobs.map(job => (
              <option key={job.id} value={job.id}>
                {job.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="card">
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Job</th>
              <th>Status</th>
              <th>Requested By</th>
              <th>Queued</th>
              <th>Started</th>
              <th>Finished</th>
              <th>Duration</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {runs.length === 0 ? (
              <tr>
                <td colSpan={9} style={{ textAlign: 'center', padding: '20px', color: '#666' }}>
                  No job runs found
                </td>
              </tr>
            ) : (
              runs.map(run => (
                <tr key={run.id}>
                  <td>{run.id}</td>
                  <td>{getJobName(run.job_id)}</td>
                  <td>
                    <span 
                      className="status" 
                      style={{ 
                        backgroundColor: getStatusColor(run.status),
                        color: getStatusTextColor(run.status)
                      }}
                    >
                      {run.status}
                    </span>
                  </td>
                  <td>User {run.requested_by}</td>
                  <td>{new Date(run.queued_at).toLocaleString()}</td>
                  <td>{run.started_at ? new Date(run.started_at).toLocaleString() : '-'}</td>
                  <td>{run.finished_at ? new Date(run.finished_at).toLocaleString() : '-'}</td>
                  <td>
                    {run.started_at ? formatDuration(run.started_at, run.finished_at) : '-'}
                  </td>
                  <td>
                    <Link 
                      to={`/job-runs/${run.id}`} 
                      className="btn btn-primary"
                      style={{ fontSize: '12px' }}
                    >
                      View Details
                    </Link>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {runs.length > 0 && (
        <div style={{ marginTop: '20px', textAlign: 'center', color: '#666' }}>
          Showing {runs.length} job runs
        </div>
      )}
    </div>
  );
};

export default JobRuns;