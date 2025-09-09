import React, { useEffect, useState } from 'react';
import { celeryApi } from '../services/api';
import { Activity, AlertCircle, CheckCircle, Users, Zap, BarChart3, Clock, TrendingUp } from 'lucide-react';

interface CeleryStatus {
  status: string;
  workers: {
    total: number;
    online: number;
    offline: number;
    details: Record<string, any>;
  };
  tasks: {
    active: number;
    registered: number;
  };
  queues: {
    queued_steps: number;
    running_steps: number;
    succeeded_steps: number;
    failed_steps: number;
  };
  timestamp: string;
  error?: string;
}

interface CeleryMetrics {
  workers: Record<string, any>;
  performance: {
    total_processed: number;
    hourly_stats: Array<{
      hour: string;
      completed_tasks: number;
      avg_duration: number;
      successful: number;
      failed: number;
    }>;
  };
  timestamp: string;
  error?: string;
}

interface CeleryQueues {
  summary: {
    total_queued: number;
    total_active: number;
    workers: number;
  };
  workers: Record<string, any>;
  step_types: Array<{
    type: string;
    queued: number;
    running: number;
    succeeded: number;
    failed: number;
    avg_duration: number;
  }>;
  timestamp: string;
  error?: string;
}

const CeleryHealthCard: React.FC = () => {
  const [status, setStatus] = useState<CeleryStatus | null>(null);
  const [metrics, setMetrics] = useState<CeleryMetrics | null>(null);
  const [queues, setQueues] = useState<CeleryQueues | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAllData = async () => {
    try {
      const [statusData, metricsData, queuesData] = await Promise.all([
        celeryApi.getStatus(),
        celeryApi.getMetrics(),
        celeryApi.getQueues()
      ]);
      
      setStatus(statusData);
      setMetrics(metricsData);
      setQueues(queuesData);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch Celery data:', err);
      setError('Failed to load Celery data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAllData();
    const interval = setInterval(fetchAllData, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="dashboard-section">
        <div className="section-header">Celery Health</div>
        <div className="compact-content">
          <div style={{ padding: '20px', textAlign: 'center', color: '#64748b' }}>
            Loading...
          </div>
        </div>
      </div>
    );
  }

  if (error || !status) {
    return (
      <div className="dashboard-section">
        <div className="section-header">Celery Health</div>
        <div className="compact-content">
          <div style={{ padding: '12px', textAlign: 'center' }}>
            <AlertCircle size={24} style={{ color: '#dc2626', marginBottom: '8px' }} />
            <div style={{ fontSize: '12px', color: '#dc2626' }}>
              {error || 'Unable to load data'}
            </div>
          </div>
        </div>
      </div>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return '#059669';
      case 'degraded': return '#d97706';
      case 'error': return '#dc2626';
      default: return '#64748b';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return <CheckCircle size={16} />;
      case 'degraded': return <AlertCircle size={16} />;
      case 'error': return <AlertCircle size={16} />;
      default: return <Activity size={16} />;
    }
  };

  // Calculate metrics data
  const recentStats = metrics?.performance.hourly_stats.slice(0, 6) || [];
  const totalRecent = recentStats.reduce((sum, stat) => sum + stat.completed_tasks, 0);
  const avgDuration = recentStats.length > 0 
    ? recentStats.reduce((sum, stat) => sum + (stat.avg_duration || 0), 0) / recentStats.length 
    : 0;
  const successRate = totalRecent > 0 
    ? (recentStats.reduce((sum, stat) => sum + stat.successful, 0) / totalRecent) * 100 
    : 0;

  // Get queue data
  const queuedTasks = queues?.summary.total_queued || status.queues.queued_steps;
  const activeTasks = queues?.summary.total_active || status.queues.running_steps;
  const totalProcessed = metrics?.performance.total_processed || 0;

  return (
    <div className="dashboard-section">
      <div className="section-header">Celery Health</div>
      <div className="compact-content">
        {/* Overall Status */}
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          marginBottom: '10px',
          padding: '6px',
          backgroundColor: status.status === 'healthy' ? '#d1fae5' : status.status === 'degraded' ? '#fef3c7' : '#fee2e2',
          borderRadius: '4px'
        }}>
          <div style={{ color: getStatusColor(status.status), marginRight: '6px' }}>
            {getStatusIcon(status.status)}
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: '12px', fontWeight: '600', color: getStatusColor(status.status) }}>
              {status.status.toUpperCase()}
            </div>
            <div style={{ fontSize: '10px', color: '#64748b' }}>
              {status.workers.online}/{status.workers.total} Workers Online
            </div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '11px', fontWeight: '600' }}>{totalProcessed.toLocaleString()}</div>
            <div style={{ fontSize: '9px', color: '#64748b' }}>Total Processed</div>
          </div>
        </div>

        {/* Key Metrics Grid */}
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: '1fr 1fr 1fr', 
          gap: '4px', 
          marginBottom: '10px',
          fontSize: '10px'
        }}>
          <div style={{ textAlign: 'center', padding: '3px', backgroundColor: '#fef3c7', borderRadius: '3px' }}>
            <div style={{ fontWeight: '600', color: '#d97706' }}>{queuedTasks}</div>
            <div style={{ color: '#64748b' }}>Queued</div>
          </div>
          <div style={{ textAlign: 'center', padding: '3px', backgroundColor: '#dbeafe', borderRadius: '3px' }}>
            <div style={{ fontWeight: '600', color: '#2563eb' }}>{activeTasks}</div>
            <div style={{ color: '#64748b' }}>Active</div>
          </div>
          <div style={{ textAlign: 'center', padding: '3px', backgroundColor: '#d1fae5', borderRadius: '3px' }}>
            <div style={{ fontWeight: '600', color: '#059669' }}>
              {successRate > 0 ? `${successRate.toFixed(0)}%` : 'N/A'}
            </div>
            <div style={{ color: '#64748b' }}>Success</div>
          </div>
        </div>

        {/* Performance Metrics */}
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
            <TrendingUp size={10} style={{ color: '#64748b' }} />
            <span style={{ fontSize: '10px', color: '#64748b' }}>Recent (6h)</span>
          </div>
          <div style={{ fontSize: '11px', fontWeight: '600' }}>
            {totalRecent}
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
            <Clock size={10} style={{ color: '#64748b' }} />
            <span style={{ fontSize: '10px', color: '#64748b' }}>Avg Duration</span>
          </div>
          <div style={{ fontSize: '11px', fontWeight: '600' }}>
            {avgDuration > 0 ? `${avgDuration.toFixed(1)}s` : 'N/A'}
          </div>
        </div>

        {/* Mini Performance Chart */}
        {recentStats.length > 0 && (
          <div style={{ marginBottom: '8px' }}>
            <div style={{ fontSize: '9px', color: '#64748b', marginBottom: '3px' }}>
              Hourly Activity
            </div>
            <div style={{ 
              display: 'flex', 
              alignItems: 'end', 
              gap: '1px', 
              height: '20px',
              backgroundColor: '#f8fafc',
              padding: '2px',
              borderRadius: '2px'
            }}>
              {recentStats.reverse().map((stat, index) => {
                const maxTasks = Math.max(...recentStats.map(s => s.completed_tasks));
                const height = maxTasks > 0 ? (stat.completed_tasks / maxTasks) * 16 : 1;
                return (
                  <div
                    key={index}
                    style={{
                      flex: 1,
                      height: `${Math.max(height, 1)}px`,
                      backgroundColor: stat.failed > stat.successful ? '#dc2626' : '#059669',
                      borderRadius: '1px',
                      opacity: 0.7
                    }}
                    title={`${stat.completed_tasks} tasks`}
                  />
                );
              })}
            </div>
          </div>
        )}

        {/* Last Updated */}
        <div style={{ 
          fontSize: '9px', 
          color: '#94a3b8', 
          textAlign: 'center',
          paddingTop: '6px',
          borderTop: '1px solid #e2e8f0'
        }}>
          Updated: {new Date(status.timestamp).toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
};

export default CeleryHealthCard;