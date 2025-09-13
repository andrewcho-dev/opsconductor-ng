import React, { useState, useEffect } from 'react';
import { healthApi } from '../services/api';

interface SystemStats {
  overall_status: string;
  services_count: number;
  healthy_services: number;
  unhealthy_services: number;
  timestamp: string;
  message: string;
  error?: string;
}

const SystemMetrics: React.FC = () => {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const fetchStats = async () => {
    try {
      setError(null);
      const result = await healthApi.getSystemStats();
      if (result.error) {
        setError(result.error);
      } else {
        setStats(result);
        setLastUpdate(new Date());
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
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <button 
          onClick={fetchStats}
          style={{ 
            background: 'none', 
            border: '1px solid #ddd', 
            padding: '2px 6px', 
            fontSize: '10px',
            borderRadius: '3px',
            cursor: 'pointer'
          }}
        >
          Refresh
        </button>
        {lastUpdate && (
          <span style={{ fontSize: '10px', color: '#666' }}>
            {lastUpdate.toLocaleTimeString()}
          </span>
        )}
      </div>

      {/* System Status - Ultra Compact */}
      <div style={{ marginBottom: '12px' }}>
        <div style={{ 
          fontSize: '11px', 
          fontWeight: '600', 
          color: '#374151', 
          marginBottom: '4px',
          textTransform: 'uppercase',
          letterSpacing: '0.5px'
        }}>
          System Status
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px', marginBottom: '8px' }}>
          <div style={{ 
            textAlign: 'center', 
            padding: '6px', 
            background: stats.overall_status === 'healthy' ? '#dcfce7' : '#fef2f2',
            borderRadius: '3px',
            border: '1px solid ' + (stats.overall_status === 'healthy' ? '#bbf7d0' : '#fecaca')
          }}>
            <div style={{ fontSize: '11px', color: '#666' }}>Overall</div>
            <div style={{ 
              fontSize: '12px', 
              fontWeight: '600',
              color: stats.overall_status === 'healthy' ? '#059669' : '#dc2626'
            }}>
              {stats.overall_status === 'healthy' ? 'Healthy' : 'Issues'}
            </div>
          </div>
          
          <div style={{ 
            textAlign: 'center', 
            padding: '6px', 
            background: '#f1f5f9',
            borderRadius: '3px',
            border: '1px solid #e2e8f0'
          }}>
            <div style={{ fontSize: '11px', color: '#666' }}>Services</div>
            <div style={{ fontSize: '12px', fontWeight: '600' }}>
              {stats.services_count} Total
            </div>
          </div>
        </div>
      </div>

      {/* Service Health Stats - Ultra Compact */}
      <div>
        <div style={{ 
          fontSize: '11px', 
          fontWeight: '600', 
          color: '#374151', 
          marginBottom: '4px',
          textTransform: 'uppercase',
          letterSpacing: '0.5px'
        }}>
          Service Health
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px' }}>
          <div style={{ 
            textAlign: 'center', 
            padding: '3px 2px', 
            background: '#dcfce7',
            borderRadius: '3px',
            border: '1px solid #bbf7d0'
          }}>
            <div style={{ fontSize: '13px', fontWeight: '600', color: '#059669' }}>
              {stats.healthy_services}
            </div>
            <div style={{ fontSize: '10px', color: '#047857' }}>Healthy</div>
          </div>
          
          <div style={{ 
            textAlign: 'center', 
            padding: '3px 2px', 
            background: stats.unhealthy_services > 0 ? '#fef2f2' : '#f8fafc',
            borderRadius: '3px',
            border: '1px solid ' + (stats.unhealthy_services > 0 ? '#fecaca' : '#e2e8f0')
          }}>
            <div style={{ 
              fontSize: '13px', 
              fontWeight: '600', 
              color: stats.unhealthy_services > 0 ? '#dc2626' : '#64748b'
            }}>
              {stats.unhealthy_services}
            </div>
            <div style={{ 
              fontSize: '10px', 
              color: stats.unhealthy_services > 0 ? '#b91c1c' : '#64748b'
            }}>
              Issues
            </div>
          </div>
        </div>
        
        {/* Status Message */}
        <div style={{ 
          marginTop: '8px', 
          padding: '4px 6px', 
          background: '#f8fafc', 
          borderRadius: '3px',
          border: '1px solid #e2e8f0'
        }}>
          <div style={{ fontSize: '10px', color: '#64748b', textAlign: 'center' }}>
            {stats.message}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemMetrics;