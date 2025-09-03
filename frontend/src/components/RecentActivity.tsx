import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { jobRunApi } from '../services/api';
import { JobRun } from '../types';
import { CheckCircle, XCircle, Play, Clock } from 'lucide-react';

const RecentActivity: React.FC = () => {
  const [recentRuns, setRecentRuns] = useState<JobRun[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRecentRuns = async () => {
      try {
        const response = await jobRunApi.list(0, 5); // Get last 5 runs only
        setRecentRuns(response.runs || []);
      } catch (error) {
        setRecentRuns([]);
      } finally {
        setLoading(false);
      }
    };

    fetchRecentRuns();
    const interval = setInterval(fetchRecentRuns, 30000);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'succeeded': return '#059669';
      case 'failed': return '#dc2626';
      case 'running': return '#1d4ed8';
      case 'queued': return '#d97706';
      default: return '#64748b';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'succeeded': return <CheckCircle size={12} />;
      case 'failed': return <XCircle size={12} />;
      case 'running': return <Play size={12} />;
      case 'queued': return <Clock size={12} />;
      default: return <Clock size={12} />;
    }
  };

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
    
    if (diffInSeconds < 60) return 'now';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h`;
    return `${Math.floor(diffInSeconds / 86400)}d`;
  };

  if (loading) return <div style={{ fontSize: '12px', color: '#666' }}>Loading...</div>;

  return (
    <div style={{ fontSize: '12px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
        <Link to="/runs" style={{ 
          fontSize: '11px', 
          color: '#1d4ed8', 
          textDecoration: 'none',
          padding: '3px 8px',
          border: '1px solid #e2e8f0',
          borderRadius: '3px'
        }}>
          View All
        </Link>
      </div>

      {(recentRuns || []).length === 0 ? (
        <div style={{ textAlign: 'center', color: '#666', padding: '12px', fontSize: '12px' }}>
          No recent job runs
        </div>
      ) : (
        <div style={{ maxHeight: '120px', overflowY: 'auto' }}>
          {(recentRuns || []).slice(0, 5).map((run) => (
            <div 
              key={run.id}
              style={{
                display: 'flex',
                alignItems: 'center',
                padding: '3px 0',
                borderBottom: '1px solid #f1f5f9'
              }}
            >
              <span 
                style={{
                  color: getStatusColor(run.status),
                  fontSize: '12px',
                  marginRight: '6px',
                  width: '12px'
                }}
              >
                {getStatusIcon(run.status)}
              </span>

              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Link 
                    to={`/job-runs/${run.id}`}
                    style={{ 
                      textDecoration: 'none', 
                      color: '#1d4ed8',
                      fontSize: '12px',
                      fontWeight: '500',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}
                  >
                    Run #{run.id}
                  </Link>
                  <span style={{ fontSize: '11px', color: '#64748b', marginLeft: '6px' }}>
                    {run.started_at ? formatTimeAgo(run.started_at) : formatTimeAgo(run.queued_at)}
                  </span>
                </div>

                <div style={{ fontSize: '11px', color: '#64748b' }}>
                  <span style={{ color: getStatusColor(run.status) }}>
                    {run.status}
                  </span>
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