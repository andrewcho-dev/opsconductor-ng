import React, { useState, useEffect } from 'react';
import { healthApi } from '../services/api';
import { 
  Globe, 
  Shield, 
  Package, 
  Zap, 
  MessageSquare, 
  Database, 
  HardDrive, 
  Users, 
  Settings, 
  Activity, 
  Monitor, 
  Server 
} from 'lucide-react';

interface ServiceStatus {
  status: string;
  service: string;
  responseTime?: number;
  error?: string;
}

interface ServiceHealthMonitorProps {
  refreshTrigger?: number;
  onLastUpdateChange?: (lastUpdate: Date | null) => void;
}

const ServiceHealthMonitor: React.FC<ServiceHealthMonitorProps> = ({ refreshTrigger, onLastUpdateChange }) => {
  const [services, setServices] = useState<Record<string, ServiceStatus>>({});
  const [loading, setLoading] = useState(true);

  // All services in a flat array
  const allServices = [
    'api-gateway', 'identity', 'asset', 'automation', 'communication',
    'postgres', 'redis', 'chromadb',
    'worker-1', 'worker-2', 'scheduler', 'celery-monitor',
    'frontend', 'nginx'
  ];

  // Get appropriate icon for each service category
  const getServiceIcon = (serviceName: string) => {
    const iconProps = { size: 12 };
    
    switch (serviceName) {
      case 'api-gateway':
        return <Globe {...iconProps} />;
      case 'identity':
        return <Shield {...iconProps} />;
      case 'asset':
        return <Package {...iconProps} />;
      case 'automation':
        return <Zap {...iconProps} />;
      case 'communication':
        return <MessageSquare {...iconProps} />;
      case 'postgres':
        return <Database {...iconProps} />;
      case 'redis':
        return <HardDrive {...iconProps} />;
      case 'chromadb':
        return <Database {...iconProps} />;
      case 'worker-1':
      case 'worker-2':
        return <Users {...iconProps} />;
      case 'scheduler':
        return <Settings {...iconProps} />;
      case 'celery-monitor':
        return <Activity {...iconProps} />;
      case 'frontend':
        return <Monitor {...iconProps} />;
      case 'nginx':
        return <Server {...iconProps} />;
      default:
        return <Server {...iconProps} />;
    }
  };

  const fetchServiceHealth = async () => {
    try {
      const results = await healthApi.checkAllServices();
      setServices(results);
      const now = new Date();
      if (onLastUpdateChange) {
        onLastUpdateChange(now);
      }
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

  // Respond to external refresh trigger
  useEffect(() => {
    if (refreshTrigger && refreshTrigger > 0) {
      fetchServiceHealth();
    }
  }, [refreshTrigger]);

  if (loading) {
    return <div style={{ fontSize: '11px', color: '#666' }}>Loading...</div>;
  }

  return (
    <div>
      {/* All services in equal-sized boxes, max 8 per row */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: `repeat(${Math.min(8, allServices.length)}, 1fr)`,
        maxWidth: '100%',
        gap: '8px'
      }}>
        {allServices.map((serviceName) => {
          const status = services[serviceName];
          
          // Determine background color based on status
          let backgroundColor = '#f3f4f6'; // Unknown/default
          let textColor = '#6b7280';
          
          if (status) {
            if (status.status === 'healthy') {
              backgroundColor = '#d1fae5';
              textColor = '#059669';
            } else if (status.status === 'unhealthy' || status.status === 'error') {
              backgroundColor = '#fee2e2';
              textColor = '#dc2626';
            } else {
              // Unknown or any other status - keep gray
              backgroundColor = '#f3f4f6';
              textColor = '#6b7280';
            }
          }
          
          return (
            <div 
              key={serviceName}
              style={{
                display: 'flex',
                flexDirection: 'row',
                alignItems: 'center',
                justifyContent: 'flex-start',
                padding: '4px 8px',
                background: backgroundColor,
                borderRadius: '4px',
                border: '1px solid #e2e8f0',
                minHeight: '32px',
                gap: '6px'
              }}
            >
              <div style={{ 
                color: textColor,
                flexShrink: 0,
                display: 'flex',
                alignItems: 'center'
              }}>
                {getServiceIcon(serviceName)}
              </div>
              <span style={{ 
                fontSize: '12px',
                fontWeight: '600',
                color: textColor,
                flex: 1,
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis'
              }}>
                {serviceName}
              </span>
              {status?.responseTime && (
                <span style={{ 
                  fontSize: '9px', 
                  color: '#666',
                  flexShrink: 0
                }}>
                  {Math.round(status.responseTime)}ms
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ServiceHealthMonitor;