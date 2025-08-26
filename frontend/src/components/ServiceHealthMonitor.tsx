import React, { useState, useEffect } from 'react';
import { healthApi } from '../services/api';

interface ServiceStatus {
  status: string;
  service: string;
  responseTime?: number;
  error?: string;
}

const ServiceHealthMonitor: React.FC = () => {
  const [services, setServices] = useState<Record<string, ServiceStatus>>({});
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const fetchServiceHealth = async () => {
    try {
      const results = await healthApi.checkAllServices();
      setServices(results);
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Failed to fetch service health:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchServiceHealth();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchServiceHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return '#28a745';
      case 'unhealthy': return '#dc3545';
      default: return '#ffc107';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return '✓';
      case 'unhealthy': return '✗';
      default: return '?';
    }
  };

  if (loading) {
    return (
      <div className="card">
        <h3>Service Health</h3>
        <div>Loading service status...</div>
      </div>
    );
  }

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
        <h3>Service Health</h3>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button 
            className="btn btn-secondary" 
            onClick={fetchServiceHealth}
            style={{ fontSize: '12px', padding: '5px 10px' }}
          >
            Refresh
          </button>
          {lastUpdate && (
            <small style={{ color: '#666' }}>
              Last updated: {lastUpdate.toLocaleTimeString()}
            </small>
          )}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '10px' }}>
        {Object.entries(services).map(([serviceName, status]) => (
          <div 
            key={serviceName}
            style={{
              padding: '10px',
              border: '1px solid #ddd',
              borderRadius: '4px',
              backgroundColor: status.status === 'healthy' ? '#f8f9fa' : '#fff5f5'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <strong style={{ textTransform: 'capitalize' }}>{serviceName}</strong>
              <span 
                style={{ 
                  color: getStatusColor(status.status),
                  fontSize: '18px',
                  fontWeight: 'bold'
                }}
              >
                {getStatusIcon(status.status)}
              </span>
            </div>
            
            <div style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
              Status: <span style={{ color: getStatusColor(status.status) }}>
                {status.status}
              </span>
            </div>
            
            {status.responseTime && (
              <div style={{ fontSize: '12px', color: '#666' }}>
                Response: {status.responseTime}ms
              </div>
            )}
            
            {status.error && (
              <div style={{ fontSize: '11px', color: '#dc3545', marginTop: '5px' }}>
                {status.error}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default ServiceHealthMonitor;