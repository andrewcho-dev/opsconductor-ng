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
  services: Record<string, AIServiceStatus>;
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
      const response = await fetch('/api/v1/ai/health', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      setHealth(data);
      setError(null);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const fetchDashboard = async () => {
    try {
      const response = await fetch('/api/v1/ai/monitoring/dashboard', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      setDashboard(data);
    } catch (err: any) {
      console.error('Dashboard fetch error:', err);
    }
  };

  const resetCircuitBreaker = async (serviceName: string) => {
    try {
      setLoading(true);
      const response = await fetch(`/api/v1/ai/circuit-breaker/reset/${serviceName}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'x-user-role': 'admin' // Add role header
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to reset circuit breaker`);
      }

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

    return () => clearInterval(interval);
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
    <div className="card">
      <div className="card-header">
        <div className="card-title-row">
          <h3 className="card-title">
            <Activity size={20} />
            AI System Monitor
          </h3>
          <div className="card-actions">
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`btn btn-sm ${autoRefresh ? 'btn-primary' : ''}`}
              title={autoRefresh ? 'Auto-refresh enabled' : 'Auto-refresh disabled'}
            >
              <RefreshCw size={14} className={autoRefresh ? 'loading-spinner' : ''} />
            </button>
            <button
              onClick={() => {
                fetchHealth();
                fetchDashboard();
              }}
              className="btn btn-sm"
              disabled={loading}
            >
              Refresh
            </button>
          </div>
        </div>
        <p className="card-subtitle">
          Real-time monitoring of AI services and performance
        </p>
      </div>

      {error && (
        <div className="alert alert-danger">
          <AlertCircle size={16} />
          {error}
        </div>
      )}

      {health && (
        <div className="ai-monitor-grid">
          {/* Overall Status */}
          <div className="monitor-section">
            <h4>System Status</h4>
            <div className={`status-badge ${health.status === 'healthy' ? 'status-success' : 'status-warning'}`}>
              {getStatusIcon(health.status)}
              <span>{health.status.toUpperCase()}</span>
            </div>
          </div>

          {/* Services Grid */}
          <div className="monitor-section">
            <h4>AI Services</h4>
            <div className="services-grid">
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
                        {(service.success_rate * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="metric">
                      <span className="metric-label">Avg Response</span>
                      <span className="metric-value">
                        {service.avg_response_time.toFixed(3)}s
                      </span>
                    </div>
                    <div className="metric">
                      <span className="metric-label">Requests</span>
                      <span className="metric-value">{service.request_count}</span>
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
                        className="btn btn-xs btn-danger"
                        disabled={loading}
                      >
                        Reset
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Alerts Section */}
          {dashboard?.analysis?.alerts && dashboard.analysis.alerts.length > 0 && (
            <div className="monitor-section">
              <h4>Active Alerts</h4>
              <div className="alerts-list">
                {dashboard.analysis.alerts.map((alert, idx) => (
                  <div key={idx} className="alert-item">
                    <div 
                      className="alert-severity"
                      style={{ color: getSeverityColor(alert.severity) }}
                    >
                      <AlertCircle size={14} />
                      {alert.severity}
                    </div>
                    <span className="alert-service">{alert.service}</span>
                    <span className="alert-message">{alert.message}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recommendations */}
          {dashboard?.analysis?.recommendations && dashboard.analysis.recommendations.length > 0 && (
            <div className="monitor-section">
              <h4>Recommendations</h4>
              <ul className="recommendations-list">
                {dashboard.analysis.recommendations.map((rec, idx) => (
                  <li key={idx}>{rec}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Statistics */}
          {dashboard?.statistics && (
            <div className="monitor-section">
              <h4>Performance Statistics</h4>
              <div className="stats-grid">
                {Object.entries(dashboard.statistics).map(([key, value]: [string, any]) => (
                  <div key={key} className="stat-card">
                    <span className="stat-label">{key.replace(/_/g, ' ')}</span>
                    <span className="stat-value">
                      {typeof value === 'number' ? value.toFixed(2) : value}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      <style jsx>{`
        .ai-monitor-grid {
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
          padding: 1rem;
        }

        .monitor-section h4 {
          margin-bottom: 0.75rem;
          color: var(--neutral-700);
          font-size: 0.875rem;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .status-badge {
          display: inline-flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.25rem 0.75rem;
          border-radius: var(--radius-md);
          font-weight: 500;
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
          grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
          gap: 1rem;
        }

        .service-card {
          background: var(--neutral-100);
          border: 1px solid var(--neutral-200);
          border-radius: var(--radius-md);
          padding: 1rem;
        }

        .service-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 0.75rem;
        }

        .service-name {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-weight: 500;
        }

        .service-type {
          font-size: 0.75rem;
          color: var(--neutral-500);
          background: var(--neutral-200);
          padding: 0.125rem 0.375rem;
          border-radius: var(--radius-sm);
        }

        .service-metrics {
          display: flex;
          gap: 1rem;
          margin-bottom: 0.75rem;
        }

        .metric {
          display: flex;
          flex-direction: column;
          flex: 1;
        }

        .metric-label {
          font-size: 0.625rem;
          color: var(--neutral-500);
          text-transform: uppercase;
        }

        .metric-value {
          font-size: 0.875rem;
          font-weight: 600;
          color: var(--neutral-700);
        }

        .circuit-breaker {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding-top: 0.5rem;
          border-top: 1px solid var(--neutral-200);
          font-size: 0.75rem;
        }

        .cb-label {
          color: var(--neutral-500);
        }

        .cb-state {
          font-weight: 600;
          text-transform: uppercase;
        }

        .alerts-list {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .alert-item {
          display: flex;
          align-items: center;
          gap: 1rem;
          padding: 0.5rem;
          background: var(--neutral-100);
          border-radius: var(--radius-sm);
        }

        .alert-severity {
          display: flex;
          align-items: center;
          gap: 0.25rem;
          font-weight: 600;
          text-transform: uppercase;
          font-size: 0.75rem;
        }

        .alert-service {
          font-weight: 500;
          color: var(--neutral-700);
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
          padding: 0.5rem 0;
          border-bottom: 1px solid var(--neutral-200);
          color: var(--neutral-600);
          font-size: 0.875rem;
        }

        .recommendations-list li:last-child {
          border-bottom: none;
        }

        .stats-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
          gap: 0.75rem;
        }

        .stat-card {
          display: flex;
          flex-direction: column;
          padding: 0.5rem;
          background: var(--neutral-100);
          border-radius: var(--radius-sm);
        }

        .stat-label {
          font-size: 0.625rem;
          color: var(--neutral-500);
          text-transform: capitalize;
        }

        .stat-value {
          font-size: 1rem;
          font-weight: 600;
          color: var(--neutral-700);
        }
      `}</style>
    </div>
  );
};

export default AIMonitor;