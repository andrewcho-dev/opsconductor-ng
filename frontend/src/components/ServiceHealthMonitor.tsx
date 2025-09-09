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

  // Group services by category
  const serviceGroups = {
    'Core Services': ['auth', 'users', 'credentials', 'targets', 'jobs'],
    'Processing': ['executor', 'scheduler', 'celery-worker', 'celery-beat'],
    'Infrastructure': ['nginx', 'frontend', 'redis', 'postgres'],
    'Monitoring': ['notification', 'discovery', 'step-libraries', 'flower']
  };

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

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {Object.entries(serviceGroups).map(([groupName, serviceList]) => (
          <div key={groupName}>
            <div style={{ 
              fontSize: '11px', 
              fontWeight: '600', 
              color: '#374151', 
              marginBottom: '4px',
              textTransform: 'uppercase',
              letterSpacing: '0.5px'
            }}>
              {groupName}
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '4px', fontSize: '12px' }}>
              {serviceList.map((serviceName) => {
                const status = services[serviceName];
                if (!status) return null;
                
                return (
                  <div 
                    key={serviceName}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '3px 6px',
                      background: status.status === 'healthy' ? '#d1fae5' : '#fee2e2',
                      borderRadius: '3px',
                      border: '1px solid #e2e8f0',
                      minHeight: '24px'
                    }}
                  >
                    <span style={{ 
                      fontWeight: '500', 
                      fontSize: '11px',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                      flex: 1
                    }}>
                      {serviceName}
                    </span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '3px', marginLeft: '4px' }}>
                      <span style={{ 
                        color: status.status === 'healthy' ? '#059669' : '#dc2626',
                        fontSize: '12px'
                      }}>
                        {status.status === 'healthy' ? <CheckCircle size={8} /> : <Circle size={8} />}
                      </span>
                      {status.responseTime && (
                        <span style={{ fontSize: '9px', color: '#666' }}>
                          {status.responseTime}ms
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ServiceHealthMonitor;