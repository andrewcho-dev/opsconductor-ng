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
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 15000);
    return () => clearInterval(interval);
  }, []);

  if (loading) return <div style={{ fontSize: '12px', color: '#666' }}>Loading...</div>;
  if (error) return <div style={{ fontSize: '12px', color: '#dc2626' }}>{error}</div>;
  if (!stats) return <div style={{ fontSize: '12px', color: '#666' }}>No data</div>;

  return (
    <div style={{ fontSize: '12px' }}>
      {/* Executor Status - Ultra Compact */}
      <div style={{ marginBottom: '8px' }}>
        <div style={{ fontWeight: '600', marginBottom: '4px', fontSize: '13px' }}>Executor</div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '4px' }}>
          <div style={{ 
            textAlign: 'center', 
            padding: '3px', 
            background: stats.worker_running ? '#dcfce7' : '#fef2f2',
            borderRadius: '3px',
            border: '1px solid ' + (stats.worker_running ? '#bbf7d0' : '#fecaca')
          }}>
            <div style={{ fontSize: '11px', color: '#666' }}>Worker</div>
            <div style={{ 
              fontSize: '12px', 
              fontWeight: '600',
              color: stats.worker_running ? '#059669' : '#dc2626'
            }}>
              {stats.worker_running ? 'Run' : 'Stop'}
            </div>
          </div>
          
          <div style={{ 
            textAlign: 'center', 
            padding: '3px', 
            background: stats.worker_enabled ? '#dcfce7' : '#fef3c7',
            borderRadius: '3px',
            border: '1px solid ' + (stats.worker_enabled ? '#bbf7d0' : '#fde68a')
          }}>
            <div style={{ fontSize: '11px', color: '#666' }}>Enabled</div>
            <div style={{ 
              fontSize: '12px', 
              fontWeight: '600',
              color: stats.worker_enabled ? '#059669' : '#d97706'
            }}>
              {stats.worker_enabled ? 'Yes' : 'No'}
            </div>
          </div>
          
          <div style={{ 
            textAlign: 'center', 
            padding: '3px', 
            background: '#f1f5f9',
            borderRadius: '3px',
            border: '1px solid #e2e8f0'
          }}>
            <div style={{ fontSize: '11px', color: '#666' }}>Poll</div>
            <div style={{ fontSize: '12px', fontWeight: '600' }}>
              {stats.poll_interval}s
            </div>
          </div>
        </div>
      </div>

      {/* Queue Stats - Ultra Compact */}
      <div>
        <div style={{ fontWeight: '600', marginBottom: '4px', fontSize: '13px' }}>Queue (24h)</div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: '3px' }}>
          <div style={{ 
            textAlign: 'center', 
            padding: '3px 2px', 
            background: '#fef3c7',
            borderRadius: '3px',
            border: '1px solid #fde68a'
          }}>
            <div style={{ fontSize: '13px', fontWeight: '600', color: '#d97706' }}>
              {stats.queue_stats.queued_steps}
            </div>
            <div style={{ fontSize: '10px', color: '#92400e' }}>Queue</div>
          </div>
          
          <div style={{ 
            textAlign: 'center', 
            padding: '3px 2px', 
            background: '#dbeafe',
            borderRadius: '3px',
            border: '1px solid #bfdbfe'
          }}>
            <div style={{ fontSize: '13px', fontWeight: '600', color: '#1d4ed8' }}>
              {stats.queue_stats.running_steps}
            </div>
            <div style={{ fontSize: '10px', color: '#1e40af' }}>Run</div>
          </div>
          
          <div style={{ 
            textAlign: 'center', 
            padding: '3px 2px', 
            background: '#dcfce7',
            borderRadius: '3px',
            border: '1px solid #bbf7d0'
          }}>
            <div style={{ fontSize: '13px', fontWeight: '600', color: '#059669' }}>
              {stats.queue_stats.succeeded_steps}
            </div>
            <div style={{ fontSize: '10px', color: '#047857' }}>OK</div>
          </div>
          
          <div style={{ 
            textAlign: 'center', 
            padding: '3px 2px', 
            background: '#fef2f2',
            borderRadius: '3px',
            border: '1px solid #fecaca'
          }}>
            <div style={{ fontSize: '13px', fontWeight: '600', color: '#dc2626' }}>
              {stats.queue_stats.failed_steps}
            </div>
            <div style={{ fontSize: '10px', color: '#b91c1c' }}>Fail</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemMetrics;