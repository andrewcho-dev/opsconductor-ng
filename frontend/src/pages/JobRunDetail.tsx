import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { jobRunApi, jobApi } from '../services/api';
import { JobRun, JobRunStep, Job } from '../types';
import { ArrowLeft } from 'lucide-react';

const JobRunDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [run, setRun] = useState<JobRun | null>(null);
  const [job, setJob] = useState<Job | null>(null);
  const [steps, setSteps] = useState<JobRunStep[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      fetchRunDetails(parseInt(id));
    }
  }, [id]);

  const fetchRunDetails = async (runId: number) => {
    try {
      const [runResponse, stepsResponse] = await Promise.all([
        jobRunApi.get(runId),
        jobRunApi.getSteps(runId)
      ]);

      setRun(runResponse);
      setSteps(stepsResponse);

      // Fetch job details
      const jobResponse = await jobApi.get(runResponse.job_id);
      setJob(jobResponse);

    } catch (error) {
      console.error('Failed to fetch run details:', error);
    } finally {
      setLoading(false);
    }
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
      case 'aborted':
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
      case 'aborted':
      case 'canceled':
        return '#6c757d';
      default:
        return '#495057';
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
      return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    } else {
      return `${seconds}s`;
    }
  };

  if (loading) return <div>Loading run details...</div>;
  if (!run) return <div>Run not found</div>;

  return (
    <div>
      <div style={{ marginBottom: '20px' }}>
        <Link to="/runs" className="btn btn-secondary"><ArrowLeft size={16} className="mr-2" />Back to Job Runs</Link>
      </div>

      <h1>Job Run #{run.id}</h1>

      {/* Run Overview */}
      <div className="card">
        <h3>Overview</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px' }}>
          <div>
            <strong>Job:</strong><br />
            {job ? job.name : `Job ${run.job_id}`}
          </div>
          <div>
            <strong>Status:</strong><br />
            <span 
              className="status" 
              style={{ 
                backgroundColor: getStatusColor(run.status),
                color: getStatusTextColor(run.status)
              }}
            >
              {run.status}
            </span>
          </div>
          <div>
            <strong>Requested By:</strong><br />
            User {run.requested_by}
          </div>
          <div>
            <strong>Correlation ID:</strong><br />
            {run.correlation_id || '-'}
          </div>
        </div>

        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
          gap: '20px',
          marginTop: '20px'
        }}>
          <div>
            <strong>Queued:</strong><br />
            {new Date(run.queued_at).toLocaleString()}
          </div>
          <div>
            <strong>Started:</strong><br />
            {run.started_at ? new Date(run.started_at).toLocaleString() : '-'}
          </div>
          <div>
            <strong>Finished:</strong><br />
            {run.finished_at ? new Date(run.finished_at).toLocaleString() : '-'}
          </div>
          <div>
            <strong>Duration:</strong><br />
            {formatDuration(run.started_at, run.finished_at)}
          </div>
        </div>

        {Object.keys(run.parameters).length > 0 && (
          <div style={{ marginTop: '20px' }}>
            <strong>Parameters:</strong>
            <pre style={{ 
              backgroundColor: '#f8f9fa', 
              padding: '10px', 
              borderRadius: '4px',
              fontSize: '12px',
              marginTop: '10px'
            }}>
              {JSON.stringify(run.parameters, null, 2)}
            </pre>
          </div>
        )}
      </div>

      {/* Job Steps */}
      <div className="card">
        <h3>Steps</h3>
        {steps.length === 0 ? (
          <p>No steps found for this run.</p>
        ) : (
          <div>
            {steps.map((step, index) => (
              <div key={step.id} style={{ 
                border: '1px solid #ddd',
                borderRadius: '4px',
                margin: '10px 0',
                padding: '15px'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                  <h4>Step {step.idx + 1}: {step.type}</h4>
                  <span 
                    className="status" 
                    style={{ 
                      backgroundColor: getStatusColor(step.status),
                      color: getStatusTextColor(step.status)
                    }}
                  >
                    {step.status}
                  </span>
                </div>

                <div style={{ 
                  display: 'grid', 
                  gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', 
                  gap: '15px',
                  marginBottom: '15px',
                  fontSize: '14px'
                }}>
                  {step.target_id && (
                    <div>
                      <strong>Target ID:</strong><br />
                      {step.target_id}
                    </div>
                  )}
                  {step.shell && (
                    <div>
                      <strong>Shell:</strong><br />
                      {step.shell}
                    </div>
                  )}
                  {step.timeoutsec && (
                    <div>
                      <strong>Timeout:</strong><br />
                      {step.timeoutsec}s
                    </div>
                  )}
                  {step.exit_code !== null && step.exit_code !== undefined && (
                    <div>
                      <strong>Exit Code:</strong><br />
                      {step.exit_code}
                    </div>
                  )}
                  {step.started_at && (
                    <div>
                      <strong>Started:</strong><br />
                      {new Date(step.started_at).toLocaleString()}
                    </div>
                  )}
                  {step.finished_at && (
                    <div>
                      <strong>Finished:</strong><br />
                      {new Date(step.finished_at).toLocaleString()}
                    </div>
                  )}
                  {step.started_at && (
                    <div>
                      <strong>Duration:</strong><br />
                      {formatDuration(step.started_at, step.finished_at)}
                    </div>
                  )}
                </div>

                {/* Output */}
                {(step.stdout || step.stderr) && (
                  <div>
                    {step.stdout && (
                      <div style={{ marginBottom: '10px' }}>
                        <strong>Output:</strong>
                        <pre style={{ 
                          backgroundColor: '#f8f9fa', 
                          padding: '10px', 
                          borderRadius: '4px',
                          fontSize: '12px',
                          maxHeight: '200px',
                          overflow: 'auto',
                          marginTop: '5px'
                        }}>
                          {step.stdout}
                        </pre>
                      </div>
                    )}
                    
                    {step.stderr && (
                      <div style={{ marginBottom: '10px' }}>
                        <strong>Error Output:</strong>
                        <pre style={{ 
                          backgroundColor: '#f8d7da', 
                          color: '#721c24',
                          padding: '10px', 
                          borderRadius: '4px',
                          fontSize: '12px',
                          maxHeight: '200px',
                          overflow: 'auto',
                          marginTop: '5px'
                        }}>
                          {step.stderr}
                        </pre>
                      </div>
                    )}
                  </div>
                )}

                {/* Metrics */}
                {step.metrics && Object.keys(step.metrics).length > 0 && (
                  <div>
                    <strong>Metrics:</strong>
                    <pre style={{ 
                      backgroundColor: '#e9ecef', 
                      padding: '10px', 
                      borderRadius: '4px',
                      fontSize: '12px',
                      marginTop: '5px'
                    }}>
                      {JSON.stringify(step.metrics, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default JobRunDetail;