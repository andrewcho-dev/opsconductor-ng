import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { jobRunApi } from '../services/api';
import { JobRun } from '../types';

const RecentActivity: React.FC = () => {
  const [recentRuns, setRecentRuns] = useState<JobRun[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRecentRuns = async () => {
      try {
        const response = await jobRunApi.list(0, 10); // Get last 10 runs
        setRecentRuns(response.runs);
      } catch (error) {
        console.error('Failed to fetch recent runs:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchRecentRuns();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchRecentRuns, 30000);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'succeeded': return '#28a745';
      case 'failed': return '#dc3545';
      case 'running': return '#007bff';
      case 'queued': return '#ffc107';
      default: return '#6c757d';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'succeeded': return '✓';
      case 'failed': return '✗';
      case 'running': return '⟳';
      case 'queued': return '⏳';
      default: return '?';
    }
  };

  const formatDuration = (startedAt: string, finishedAt?: string) => {
    const start = new Date(startedAt);
    const end = finishedAt ? new Date(finishedAt) : new Date();
    const duration = Math.floor((end.getTime() - start.getTime()) / 1000);
    
    if (duration < 60) return `${duration}s`;
    if (duration < 3600) return `${Math.floor(duration / 60)}m ${duration % 60}s`;
    return `${Math.floor(duration / 3600)}h ${Math.floor((duration % 3600) / 60)}m`;
  };

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
    
    if (diffInSeconds < 60) return 'Just now';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
    return `${Math.floor(diffInSeconds / 86400)}d ago`;
  };

  if (loading) {
    return (
      <div className="card">
        <h3>Recent Activity</h3>
        <div>Loading recent job runs...</div>
      </div>
    );
  }

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
        <h3>Recent Activity</h3>
        <Link to="/runs" className="btn btn-secondary" style={{ fontSize: '12px', padding: '5px 10px' }}>
          View All
        </Link>
      </div>

      {recentRuns.length === 0 ? (
        <div style={{ textAlign: 'center', color: '#666', padding: '20px' }}>
          No recent job runs
        </div>
      ) : (
        <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
          {recentRuns.map((run) => (
            <div 
              key={run.id}
              style={{
                display: 'flex',
                alignItems: 'center',
                padding: '10px',
                borderBottom: '1px solid #eee',
                transition: 'background-color 0.2s'
              }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f8f9fa'}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
            >
              <div 
                style={{
                  width: '30px',
                  height: '30px',
                  borderRadius: '50%',
                  backgroundColor: getStatusColor(run.status),
                  color: 'white',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '14px',
                  marginRight: '12px'
                }}
              >
                {getStatusIcon(run.status)}
              </div>

              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Link 
                    to={`/runs/${run.id}`}
                    style={{ 
                      textDecoration: 'none', 
                      color: '#007bff',
                      fontWeight: 'bold',
                      fontSize: '14px'
                    }}
                  >
                    Job Run #{run.id}
                  </Link>
                  <span style={{ fontSize: '12px', color: '#666' }}>
                    {run.started_at ? formatTimeAgo(run.started_at) : formatTimeAgo(run.queued_at)}
                  </span>
                </div>

                <div style={{ fontSize: '12px', color: '#666', marginTop: '2px' }}>
                  <span style={{ textTransform: 'capitalize', color: getStatusColor(run.status) }}>
                    {run.status}
                  </span>
                  {run.started_at && (
                    <>
                      {' • '}
                      Duration: {formatDuration(run.started_at, run.finished_at || undefined)}
                    </>
                  )}
                  {run.parameters && Object.keys(run.parameters).length > 0 && (
                    <>
                      {' • '}
                      {Object.keys(run.parameters).length} parameter(s)
                    </>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default RecentActivity;