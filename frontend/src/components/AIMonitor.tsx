import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  AlertCircle, 
  CheckCircle, 
  XCircle, 
  RefreshCw, 
  TrendingUp,
  TrendingDown,
  Zap,
  Clock,
  Server
} from 'lucide-react';
import { aiApi } from '../services/api';

interface AIServiceStatus {
  status: string;
  url: string;
  service_type: string;
  circuit_breaker: string;
  success_rate: number;
  avg_response_time: number;
  request_count: number;
}

interface AIHealth {
  status: string;
  service?: string;
  architecture?: string;
  brain_engine?: {
    status: string;
    brain_type: string;
  };
  services?: Record<string, AIServiceStatus>;
  timestamp: string;
}

interface DashboardData {
  current: {
    services: Record<string, any>;
    overall_health: string;
  };
  history: any[];
  analysis: {
    overall_health: string;
    alerts: Array<{
      severity: string;
      service: string;
      message: string;
    }>;
    recommendations: string[];
  };
  statistics: Record<string, any>;
}

const AIMonitor: React.FC = () => {
  const [health, setHealth] = useState<AIHealth | null>(null);
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchHealth = async () => {
    try {
      const data = await aiApi.health();
      console.log('AI Health data received:', data);
      setHealth(data);
      setError(null);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const fetchDashboard = async () => {
    try {
      const data = await aiApi.monitoringDashboard();
      setDashboard(data);
    } catch (err: any) {
      console.error('Dashboard fetch error:', err);
    }
  };

  const resetCircuitBreaker = async (serviceName: string) => {
    try {
      setLoading(true);
      await aiApi.resetCircuitBreaker(serviceName);
      // Refresh health status
      await fetchHealth();
    } catch (err: any) {
      alert(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    fetchDashboard();

    // Auto-refresh
    const interval = setInterval(() => {
      if (autoRefresh) {
        fetchHealth();
        fetchDashboard();
      }
    }, 30000); // 30 seconds

    // Listen for external refresh events
    const handleRefresh = () => {
      fetchHealth();
      fetchDashboard();
    };
    window.addEventListener('refreshAIMonitor', handleRefresh);

    return () => {
      clearInterval(interval);
      window.removeEventListener('refreshAIMonitor', handleRefresh);
    };
  }, [autoRefresh]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle size={16} style={{ color: 'var(--success-green)' }} />;
      case 'unhealthy':
        return <XCircle size={16} style={{ color: 'var(--danger-red)' }} />;
      case 'unavailable':
        return <AlertCircle size={16} style={{ color: 'var(--neutral-400)' }} />;
      default:
        return <Activity size={16} style={{ color: 'var(--neutral-400)' }} />;
    }
  };

  const getCircuitBreakerColor = (state: string) => {
    switch (state) {
      case 'closed':
        return 'var(--success-green)';
      case 'open':
        return 'var(--danger-red)';
      case 'half_open':
        return 'var(--warning-orange)';
      default:
        return 'var(--neutral-400)';
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
      case 'error':
        return 'var(--danger-red)';
      case 'warning':
        return 'var(--warning-orange)';
      case 'info':
        return 'var(--primary-blue)';
      default:
        return 'var(--neutral-600)';
    }
  };

  return (
    <div className="ai-monitor-container">
      <style>
        {`
          /* AI Monitor styles - conforming to site visual standards */
          .ai-monitor-container {
            font-size: 13px;
          }
          .monitor-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid var(--neutral-200);
          }
          .monitor-title {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 14px;
            font-weight: 600;
            color: var(--neutral-800);
            margin: 0;
          }
          .monitor-actions {
            display: flex;
            gap: 4px;
          }
          .btn-icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 24px;
            height: 24px;
            border: none;
            background: none;
            cursor: pointer;
            transition: all 0.15s;
            margin: 0 1px;
            padding: 2px;
            color: var(--neutral-500);
          }
          .btn-icon:hover {
            color: var(--neutral-700);
          }
          .btn-icon.active {
            color: var(--primary-blue);
          }
          .btn-small {
            padding: 4px 8px;
            border: 1px solid var(--neutral-300);
            border-radius: 4px;
            background: white;
            cursor: pointer;
            font-size: 11px;
            font-weight: 500;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 4px;
          }
          .btn-small:hover {
            background: var(--neutral-50);
          }
          .btn-small:disabled {
            opacity: 0.5;
            cursor: not-allowed;
          }
          .error-message {
            background: var(--danger-red-light);
            color: var(--danger-red);
            padding: 8px 12px;
            border-radius: 4px;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 12px;
          }
          .monitor-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 12px;
          }
          .monitor-section {
            background: var(--neutral-50);
            border: 1px solid var(--neutral-200);
            border-radius: 6px;
            overflow: hidden;
          }
          .section-header {
            background: var(--neutral-100);
            padding: 8px 12px;
            font-weight: 600;
            font-size: 12px;
            color: var(--neutral-700);
            border-bottom: 1px solid var(--neutral-200);
            text-transform: uppercase;
            letter-spacing: 0.5px;
          }
          .section-content {
            padding: 8px 12px;
          }
          .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 12px;
            border-radius: 12px;
            font-weight: 500;
            font-size: 12px;
          }
          .status-success {
            background: var(--success-green-light);
            color: var(--success-green);
          }
          .status-warning {
            background: var(--warning-orange-light);
            color: var(--warning-orange);
          }
          .services-grid {
            display: grid;
            grid-template-columns: repeat(10, 1fr);
            gap: 8px;
          }
          .section-header-small {
            font-weight: 600;
            font-size: 12px;
            color: var(--neutral-700);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
            padding-bottom: 4px;
            border-bottom: 1px solid var(--neutral-200);
          }
          .alerts-section, .stats-section {
            background: var(--neutral-50);
            border: 1px solid var(--neutral-200);
            border-radius: 4px;
            padding: 8px;
          }
          .service-card {
            background: white;
            border: 1px solid var(--neutral-200);
            border-radius: 4px;
            padding: 8px;
            grid-column: span 2;
          }
          .service-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
          }
          .service-name {
            display: flex;
            align-items: center;
            gap: 6px;
            font-weight: 500;
            font-size: 12px;
          }
          .service-type {
            font-size: 10px;
            color: var(--neutral-500);
            background: var(--neutral-200);
            padding: 2px 6px;
            border-radius: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
          }
          .service-metrics {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 8px;
            margin-bottom: 8px;
          }
          .metric {
            display: flex;
            flex-direction: column;
          }
          .metric-label {
            font-size: 10px;
            color: var(--neutral-500);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 2px;
          }
          .metric-value {
            font-size: 12px;
            font-weight: 600;
            color: var(--neutral-800);
          }
          .circuit-breaker {
            display: flex;
            align-items: center;
            gap: 6px;
            padding-top: 6px;
            border-top: 1px solid var(--neutral-200);
            font-size: 11px;
          }
          .cb-label {
            color: var(--neutral-500);
          }
          .cb-state {
            font-weight: 600;
            text-transform: uppercase;
          }
          .btn-reset {
            padding: 2px 6px;
            border: 1px solid var(--danger-red);
            border-radius: 3px;
            background: white;
            color: var(--danger-red);
            cursor: pointer;
            font-size: 10px;
            font-weight: 500;
            transition: all 0.2s;
          }
          .btn-reset:hover {
            background: var(--danger-red);
            color: white;
          }
          .alerts-list {
            display: flex;
            flex-direction: column;
            gap: 6px;
          }
          .alert-item {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 6px 8px;
            background: white;
            border-radius: 4px;
            border-left: 3px solid var(--neutral-300);
            font-size: 11px;
          }
          .alert-severity {
            display: flex;
            align-items: center;
            gap: 4px;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 10px;
            min-width: 60px;
          }
          .alert-service {
            font-weight: 500;
            color: var(--neutral-700);
            min-width: 80px;
          }
          .alert-message {
            flex: 1;
            color: var(--neutral-600);
          }
          .recommendations-list {
            list-style: none;
            padding: 0;
            margin: 0;
          }
          .recommendations-list li {
            padding: 6px 0;
            border-bottom: 1px solid var(--neutral-200);
            color: var(--neutral-600);
            font-size: 12px;
          }
          .recommendations-list li:last-child {
            border-bottom: none;
          }
          .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
            gap: 8px;
          }
          .stat-card {
            display: flex;
            flex-direction: column;
            padding: 6px 8px;
            background: white;
            border-radius: 4px;
            border: 1px solid var(--neutral-200);
          }
          .stat-label {
            font-size: 10px;
            color: var(--neutral-500);
            text-transform: capitalize;
            margin-bottom: 2px;
          }
          .stat-value {
            font-size: 13px;
            font-weight: 600;
            color: var(--neutral-800);
          }
        `}
      </style>



      {error && (
        <div className="error-message">
          <AlertCircle size={14} />
          {error}
        </div>
      )}

      {health && (
        <div className="monitor-section">
          <div className="section-header">AI Service Status</div>
          <div className="section-content">
            <div className="service-card">
              <div className="service-header">
                <div className="service-name">
                  {getStatusIcon(health.status)}
                  <span>{health.service || 'AI Service'}</span>
                </div>
                <span className="service-type">{health.architecture || 'N/A'}</span>
              </div>
              
              <div className="service-metrics">
                <div className="metric">
                  <span className="metric-label">Status</span>
                  <span className="metric-value">{health.status}</span>
                </div>
                <div className="metric">
                  <span className="metric-label">Brain Type</span>
                  <span className="metric-value">{health.brain_engine?.brain_type || 'N/A'}</span>
                </div>
                <div className="metric">
                  <span className="metric-label">Architecture</span>
                  <span className="metric-value">{health.architecture || 'N/A'}</span>
                </div>
              </div>
              
              {health.timestamp && (
                <div className="circuit-breaker">
                  <span className="cb-label">Last Updated:</span>
                  <span className="cb-state">
                    {new Date(health.timestamp).toLocaleTimeString()}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {health && health.services && (
        <div className="services-grid">
          {/* Direct service cards as subcards */}
          {Object.entries(health.services).map(([name, service]) => (
            <div key={name} className="service-card">
              <div className="service-header">
                <div className="service-name">
                  {getStatusIcon(service.status)}
                  <span>{name}</span>
                </div>
                <span className="service-type">{service.service_type}</span>
              </div>
              
              <div className="service-metrics">
                <div className="metric">
                  <span className="metric-label">Success Rate</span>
                  <span className="metric-value">
                    {service.success_rate != null ? (service.success_rate * 100).toFixed(1) : '0.0'}%
                  </span>
                </div>
                <div className="metric">
                  <span className="metric-label">Avg Response</span>
                  <span className="metric-value">
                    {service.avg_response_time != null ? service.avg_response_time.toFixed(3) : '0.000'}s
                  </span>
                </div>
                <div className="metric">
                  <span className="metric-label">Requests</span>
                  <span className="metric-value">{service.request_count ?? 0}</span>
                </div>
              </div>

              <div className="circuit-breaker">
                <span className="cb-label">Circuit Breaker:</span>
                <span 
                  className="cb-state"
                  style={{ color: getCircuitBreakerColor(service.circuit_breaker) }}
                >
                  {service.circuit_breaker}
                </span>
                {service.circuit_breaker === 'open' && (
                  <button
                    onClick={() => resetCircuitBreaker(name)}
                    className="btn-reset"
                    disabled={loading}
                  >
                    Reset
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Alerts Section - Disabled */}
      {false && dashboard?.analysis?.alerts && (dashboard?.analysis?.alerts?.length || 0) > 0 && (
        <div className="alerts-section" style={{ marginTop: '12px' }}>
          <div className="section-header-small">Active Alerts</div>
          <div className="alerts-list">
            {dashboard?.analysis?.alerts?.map((alert, idx) => (
              <div key={idx} className="alert-item">
                <div 
                  className="alert-severity"
                  style={{ color: getSeverityColor(alert.severity) }}
                >
                  <AlertCircle size={12} />
                  {alert.severity}
                </div>
                <span className="alert-service">{alert.service}</span>
                <span className="alert-message">{alert.message}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Statistics - Keep this */}
      {dashboard?.statistics && Object.keys(dashboard.statistics).length > 0 && (
        <div className="stats-section" style={{ marginTop: '12px' }}>
          <div className="section-header-small">Performance Statistics</div>
          <div className="stats-grid">
            {Object.entries(dashboard.statistics).map(([key, value]: [string, any]) => (
              <div key={key} className="stat-card">
                <span className="stat-label">{key.replace(/_/g, ' ')}</span>
                <span className="stat-value">
                  {typeof value === 'number' && value != null ? value.toFixed(2) : (value ?? 'N/A')}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default AIMonitor;