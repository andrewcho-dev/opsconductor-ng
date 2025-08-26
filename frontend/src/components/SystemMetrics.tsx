import React, { useState, useEffect } from 'react';
import { healthApi } from '../services/api';

interface QueueStats {
  queued_steps: number;
  running_steps: number;
  succeeded_steps: number;
  failed_steps: number;
}

interface SystemStats {
  worker_running: boolean;
  worker_enabled: boolean;
  poll_interval: number;
  queue_stats: QueueStats;
}

const SystemMetrics: React.FC = () => {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = async () => {
    try {
      setError(null);
      const result = await healthApi.getSystemStats();
      if (result.error) {
        setError(result.error);
      } else {
        setStats(result);
      }
    } catch (err) {
      setError('Failed to fetch system metrics');
      console.error('System metrics error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    
    // Auto-refresh every 15 seconds
    const interval = setInterval(fetchStats, 15000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="card">
        <h3>System Metrics</h3>
        <div>Loading system metrics...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card">
        <h3>System Metrics</h3>
        <div style={{ color: '#dc3545' }}>
          {error}
          <button 
            className="btn btn-secondary" 
            onClick={fetchStats}
            style={{ marginLeft: '10px', fontSize: '12px' }}
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="card">
        <h3>System Metrics</h3>
        <div>No data available</div>
      </div>
    );
  }

  const totalSteps = stats.queue_stats.queued_steps + stats.queue_stats.running_steps + 
                   stats.queue_stats.succeeded_steps + stats.queue_stats.failed_steps;

  return (
    <div className="card">
      <h3>System Metrics</h3>
      
      {/* Worker Status */}
      <div style={{ marginBottom: '20px' }}>
        <h4 style={{ fontSize: '16px', marginBottom: '10px' }}>Executor Status</h4>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '10px' }}>
          <div style={{ textAlign: 'center', padding: '10px', backgroundColor: '#f8f9fa', borderRadius: '4px' }}>
            <div style={{ fontSize: '12px', color: '#666' }}>Worker</div>
            <div style={{ 
              fontSize: '14px', 
              fontWeight: 'bold',
              color: stats.worker_running ? '#28a745' : '#dc3545'
            }}>
              {stats.worker_running ? 'Running' : 'Stopped'}
            </div>
          </div>
          
          <div style={{ textAlign: 'center', padding: '10px', backgroundColor: '#f8f9fa', borderRadius: '4px' }}>
            <div style={{ fontSize: '12px', color: '#666' }}>Enabled</div>
            <div style={{ 
              fontSize: '14px', 
              fontWeight: 'bold',
              color: stats.worker_enabled ? '#28a745' : '#ffc107'
            }}>
              {stats.worker_enabled ? 'Yes' : 'No'}
            </div>
          </div>
          
          <div style={{ textAlign: 'center', padding: '10px', backgroundColor: '#f8f9fa', borderRadius: '4px' }}>
            <div style={{ fontSize: '12px', color: '#666' }}>Poll Interval</div>
            <div style={{ fontSize: '14px', fontWeight: 'bold' }}>
              {stats.poll_interval}s
            </div>
          </div>
        </div>
      </div>

      {/* Queue Statistics */}
      <div>
        <h4 style={{ fontSize: '16px', marginBottom: '10px' }}>Queue Statistics (24h)</h4>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '10px' }}>
          <div style={{ textAlign: 'center', padding: '10px', backgroundColor: '#fff3cd', borderRadius: '4px' }}>
            <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#856404' }}>
              {stats.queue_stats.queued_steps}
            </div>
            <div style={{ fontSize: '12px', color: '#856404' }}>Queued</div>
          </div>
          
          <div style={{ textAlign: 'center', padding: '10px', backgroundColor: '#cce5ff', borderRadius: '4px' }}>
            <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#004085' }}>
              {stats.queue_stats.running_steps}
            </div>
            <div style={{ fontSize: '12px', color: '#004085' }}>Running</div>
          </div>
          
          <div style={{ textAlign: 'center', padding: '10px', backgroundColor: '#d4edda', borderRadius: '4px' }}>
            <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#155724' }}>
              {stats.queue_stats.succeeded_steps}
            </div>
            <div style={{ fontSize: '12px', color: '#155724' }}>Succeeded</div>
          </div>
          
          <div style={{ textAlign: 'center', padding: '10px', backgroundColor: '#f8d7da', borderRadius: '4px' }}>
            <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#721c24' }}>
              {stats.queue_stats.failed_steps}
            </div>
            <div style={{ fontSize: '12px', color: '#721c24' }}>Failed</div>
          </div>
        </div>
        
        {totalSteps > 0 && (
          <div style={{ marginTop: '10px', fontSize: '12px', color: '#666' }}>
            Total steps processed: {totalSteps}
          </div>
        )}
      </div>
    </div>
  );
};

export default SystemMetrics;