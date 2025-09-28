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
  Server,
  Brain,
  Bot,
  Search,
  Cpu,
  Network,
  Clock,
  Eye,
  Layers,
  Gauge,
  MemoryStick
} from 'lucide-react';

interface ServiceStatus {
  status: string;
  service: string;
  responseTime?: number;
  error?: string;
  details?: Record<string, any>;
}

interface ServiceHealthMonitorProps {
  refreshTrigger?: number;
  onLastUpdateChange?: (lastUpdate: Date | null) => void;
}

const ServiceHealthMonitor: React.FC<ServiceHealthMonitorProps> = ({ refreshTrigger, onLastUpdateChange }) => {
  const [services, setServices] = useState<Record<string, ServiceStatus>>({});
  const [loading, setLoading] = useState(true);

  // Get services dynamically from the API response
  const allServices = Object.keys(services).sort();

  // Get appropriate icon for each service category
  const getServiceIcon = (serviceName: string) => {
    const iconProps = { size: 12 };
    
    switch (serviceName) {
      // Core Services
      case 'api-gateway':
        return <Globe {...iconProps} />;
      case 'identity-service':
        return <Shield {...iconProps} />;
      case 'asset-service':
        return <Package {...iconProps} />;
      case 'automation-service':
        return <Zap {...iconProps} />;
      case 'communication-service':
        return <MessageSquare {...iconProps} />;
      
      // AI Services
      case 'ai-brain':
        return <Bot {...iconProps} />;
      
      // Infrastructure
      case 'postgres':
        return <Database {...iconProps} />;
      case 'redis':
        return <HardDrive {...iconProps} />;
      case 'chromadb':
        return <Layers {...iconProps} />;
      case 'ollama':
        return <Bot {...iconProps} />;
      
      // Workers & Monitoring
      case 'worker-1':
      case 'worker-2':
        return <Users {...iconProps} />;
      case 'scheduler':
        return <Clock {...iconProps} />;
      case 'celery-monitor':
        return <Eye {...iconProps} />;
      
      // Frontend & Proxy
      case 'frontend':
        return <Monitor {...iconProps} />;
      
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
      {/* All services in equal-sized boxes, max 10 per row */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: `repeat(${Math.min(10, allServices.length)}, 1fr)`,
        maxWidth: '100%',
        gap: '6px'
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
            } else if (status.status === 'unknown') {
              backgroundColor = '#fef3c7';
              textColor = '#d97706';
            } else {
              // Any other status - keep gray
              backgroundColor = '#f3f4f6';
              textColor = '#6b7280';
            }
          }
          
          // Create tooltip content
          const getTooltipContent = () => {
            if (!status) return `${serviceName}: No data`;
            
            let tooltip = `${serviceName}: ${status.status}`;
            if (status.responseTime) tooltip += `\nResponse: ${Math.round(status.responseTime)}ms`;
            if (status.details?.usage) tooltip += `\nUsage: ${status.details.usage}`;
            if (status.details?.utilization) tooltip += `\nGPU: ${status.details.utilization}`;
            if (status.details?.memory) tooltip += `\nGPU Memory: ${status.details.memory}`;
            if (status.error) tooltip += `\nError: ${status.error}`;
            
            return tooltip;
          };
          
          return (
            <div 
              key={serviceName}
              title={getTooltipContent()}
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
                gap: '6px',
                cursor: 'help'
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
              {/* Show response time or resource usage */}
              {status?.responseTime && (
                <span style={{ 
                  fontSize: '9px', 
                  color: '#666',
                  flexShrink: 0
                }}>
                  {Math.round(status.responseTime)}ms
                </span>
              )}
              {status?.details?.usage && (
                <span style={{ 
                  fontSize: '9px', 
                  color: textColor,
                  flexShrink: 0,
                  fontWeight: '600'
                }}>
                  {status.details.usage}
                </span>
              )}
              {status?.details?.utilization && (
                <span style={{ 
                  fontSize: '9px', 
                  color: textColor,
                  flexShrink: 0,
                  fontWeight: '600'
                }}>
                  {status.details.utilization}
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