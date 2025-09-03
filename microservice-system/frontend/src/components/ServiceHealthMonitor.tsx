import React, { useState, useEffect } from 'react';
import { healthApi } from '../services/api';
import { CheckCircle, Circle } from 'lucide-react';

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
    const interval = setInterval(fetchServiceHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <div style={{ fontSize: '11px', color: '#666' }}>Loading...</div>;
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <button 
          onClick={fetchServiceHealth}
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

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '6px', fontSize: '12px' }}>
        {Object.entries(services).map(([serviceName, status]) => (
          <div 
            key={serviceName}
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '4px 8px',
              background: status.status === 'healthy' ? '#f0f9ff' : '#fef2f2',
              borderRadius: '3px',
              border: '1px solid ' + (status.status === 'healthy' ? '#e0f2fe' : '#fecaca')
            }}
          >
            <span style={{ fontWeight: '500', fontSize: '12px' }}>{serviceName}</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span style={{ 
                color: status.status === 'healthy' ? '#059669' : '#dc2626',
                fontSize: '14px'
              }}>
                {status.status === 'healthy' ? <CheckCircle size={10} /> : <Circle size={10} />}
              </span>
              {status.responseTime && (
                <span style={{ fontSize: '11px', color: '#666' }}>
                  {status.responseTime}ms
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ServiceHealthMonitor;