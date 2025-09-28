import React, { useState, useEffect } from 'react';
import { 
  Server, 
  Cpu, 
  HardDrive, 
  Activity, 
  Wifi,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  TrendingUp,
  TrendingDown,
  Database,
  Monitor,
  Zap
} from 'lucide-react';

interface SystemMetric {
  id: string;
  name: string;
  value: number;
  unit: string;
  status: 'healthy' | 'warning' | 'critical';
  trend: 'up' | 'down' | 'stable';
  lastUpdated: string;
}

interface Service {
  id: string;
  name: string;
  type: 'database' | 'api' | 'worker' | 'cache' | 'queue';
  status: 'running' | 'stopped' | 'error' | 'starting';
  uptime: number;
  responseTime: number;
  lastCheck: string;
  url?: string;
}

interface Alert {
  id: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  title: string;
  message: string;
  timestamp: string;
  acknowledged: boolean;
  source: string;
}

const InfrastructureMonitoring: React.FC = () => {
  const [metrics, setMetrics] = useState<SystemMetric[]>([]);
  const [services, setServices] = useState<Service[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'services' | 'alerts'>('overview');

  const fetchHealthData = async () => {
    try {
      setLoading(true);
      
      // Fetch real data from health monitoring API via host port
      const [metricsResponse, servicesResponse, alertsResponse] = await Promise.all([
        fetch('http://192.168.10.50:3004/health/metrics'),
        fetch('http://192.168.10.50:3004/health/services'),
        fetch('http://192.168.10.50:3004/health/alerts')
      ]);

      if (metricsResponse.ok) {
        const metricsData = await metricsResponse.json();
        setMetrics(metricsData.metrics || []);
      }

      if (servicesResponse.ok) {
        const servicesData = await servicesResponse.json();
        setServices(servicesData.services || []);
      }

      if (alertsResponse.ok) {
        const alertsData = await alertsResponse.json();
        setAlerts(alertsData.alerts || []);
      }

    } catch (error) {
      console.error('Failed to fetch health data:', error);
      // Set empty arrays on error instead of mock data
      setMetrics([]);
      setServices([]);
      setAlerts([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealthData();
    
    // Refresh data every 30 seconds
    const interval = setInterval(fetchHealthData, 30000);
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
      case 'healthy':
        return <CheckCircle className="text-success" size={16} />;
      case 'warning':
        return <AlertTriangle className="text-warning" size={16} />;
      case 'error':
      case 'critical':
        return <XCircle className="text-danger" size={16} />;
      case 'stopped':
        return <Clock className="text-secondary" size={16} />;
      case 'starting':
        return <Activity className="text-info" size={16} />;
      default:
        return <AlertTriangle className="text-secondary" size={16} />;
    }
  };

  const getStatusBadge = (status: string) => {
    const baseClass = "badge rounded-pill";
    switch (status) {
      case 'running':
      case 'healthy':
        return `${baseClass} bg-success`;
      case 'warning':
        return `${baseClass} bg-warning`;
      case 'error':
      case 'critical':
        return `${baseClass} bg-danger`;
      case 'stopped':
        return `${baseClass} bg-secondary`;
      case 'starting':
        return `${baseClass} bg-info`;
      default:
        return `${baseClass} bg-secondary`;
    }
  };

  const getSeverityBadge = (severity: string) => {
    const baseClass = "badge rounded-pill";
    switch (severity) {
      case 'info':
        return `${baseClass} bg-info`;
      case 'warning':
        return `${baseClass} bg-warning`;
      case 'error':
        return `${baseClass} bg-danger`;
      case 'critical':
        return `${baseClass} bg-danger`;
      default:
        return `${baseClass} bg-secondary`;
    }
  };

  const getServiceIcon = (type: string) => {
    switch (type) {
      case 'database':
        return <Database size={20} />;
      case 'api':
        return <Server size={20} />;
      case 'worker':
        return <Cpu size={20} />;
      case 'cache':
        return <Zap size={20} />;
      case 'queue':
        return <Activity size={20} />;
      default:
        return <Monitor size={20} />;
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="text-danger" size={14} />;
      case 'down':
        return <TrendingDown className="text-success" size={14} />;
      default:
        return null;
    }
  };

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (days > 0) return `${days}d ${hours}h`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getTimeAgo = (dateString: string) => {
    const now = new Date();
    const date = new Date(dateString);
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  };

  if (loading) {
    return (
      <div className="container-fluid py-4">
        <div className="d-flex justify-content-center align-items-center" style={{ minHeight: '400px' }}>
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container-fluid py-4">
      <div className="row mb-4">
        <div className="col">
          <div className="d-flex justify-content-between align-items-center">
            <div>
              <h1 className="h3 mb-1">Infrastructure Monitoring</h1>
              <p className="text-muted mb-0">Monitor system health and service status</p>
            </div>
            <div className="d-flex gap-2">
              <button 
                className="btn btn-outline-primary"
                onClick={fetchHealthData}
                disabled={loading}
              >
                <Activity size={16} className="me-2" />
                Refresh
              </button>
              <button className="btn btn-primary">
                <AlertTriangle size={16} className="me-2" />
                Configure Alerts
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Alert Summary */}
      {alerts.filter(a => !a.acknowledged && a.severity !== 'info').length > 0 && (
        <div className="row mb-4">
          <div className="col">
            <div className="alert alert-warning d-flex align-items-center">
              <AlertTriangle size={20} className="me-2" />
              <div className="flex-grow-1">
                <strong>Active Alerts:</strong> {alerts.filter(a => !a.acknowledged && a.severity !== 'info').length} unacknowledged alerts require attention
              </div>
              <button 
                className="btn btn-sm btn-outline-warning"
                onClick={() => setActiveTab('alerts')}
              >
                View All
              </button>
            </div>
          </div>
        </div>
      )}

      {/* System Metrics */}
      <div className="row mb-4">
        {metrics.map((metric) => (
          <div key={metric.id} className="col-md-3 mb-3">
            <div className="card border-0 shadow-sm">
              <div className="card-body">
                <div className="d-flex align-items-center justify-content-between mb-2">
                  <div className="d-flex align-items-center">
                    {metric.name === 'CPU Usage' && <Cpu className="text-primary me-2" size={20} />}
                    {metric.name === 'Memory Usage' && <Activity className="text-info me-2" size={20} />}
                    {metric.name === 'Disk Usage' && <HardDrive className="text-success me-2" size={20} />}
                    {metric.name === 'Network I/O' && <Wifi className="text-warning me-2" size={20} />}
                    <span className="fw-semibold small">{metric.name}</span>
                  </div>
                  {getTrendIcon(metric.trend)}
                </div>
                <div className="d-flex align-items-end justify-content-between">
                  <div>
                    <div className="h4 mb-0">{metric.value}{metric.unit}</div>
                    <span className={getStatusBadge(metric.status)}>
                      {getStatusIcon(metric.status)}
                      <span className="ms-1">{metric.status}</span>
                    </span>
                  </div>
                  <div className="progress" style={{ width: '60px', height: '6px' }}>
                    <div 
                      className={`progress-bar ${
                        metric.status === 'healthy' ? 'bg-success' : 
                        metric.status === 'warning' ? 'bg-warning' : 'bg-danger'
                      }`}
                      style={{ width: `${Math.min(metric.value, 100)}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="card border-0 shadow-sm">
        <div className="card-header bg-white border-bottom">
          <ul className="nav nav-tabs card-header-tabs">
            <li className="nav-item">
              <button 
                className={`nav-link ${activeTab === 'overview' ? 'active' : ''}`}
                onClick={() => setActiveTab('overview')}
              >
                <Monitor size={16} className="me-2" />
                Overview
              </button>
            </li>
            <li className="nav-item">
              <button 
                className={`nav-link ${activeTab === 'services' ? 'active' : ''}`}
                onClick={() => setActiveTab('services')}
              >
                <Server size={16} className="me-2" />
                Services ({services.filter(s => s.status === 'running').length}/{services.length})
              </button>
            </li>
            <li className="nav-item">
              <button 
                className={`nav-link ${activeTab === 'alerts' ? 'active' : ''}`}
                onClick={() => setActiveTab('alerts')}
              >
                <AlertTriangle size={16} className="me-2" />
                Alerts ({alerts.filter(a => !a.acknowledged).length})
              </button>
            </li>
          </ul>
        </div>

        <div className="card-body">
          {activeTab === 'overview' && (
            <div className="row">
              <div className="col-md-8">
                <h5 className="mb-3">System Health Overview</h5>
                <div className="row">
                  <div className="col-md-6">
                    <div className="card bg-light border-0 mb-3">
                      <div className="card-body">
                        <div className="d-flex align-items-center">
                          <CheckCircle className="text-success me-3" size={24} />
                          <div>
                            <div className="fw-semibold">Services Running</div>
                            <div className="text-muted small">
                              {services.filter(s => s.status === 'running').length} of {services.length} services operational
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="col-md-6">
                    <div className="card bg-light border-0 mb-3">
                      <div className="card-body">
                        <div className="d-flex align-items-center">
                          <Activity className="text-info me-3" size={24} />
                          <div>
                            <div className="fw-semibold">System Load</div>
                            <div className="text-muted small">
                              Average response time: {Math.round(services.reduce((acc, s) => acc + s.responseTime, 0) / services.length)}ms
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div className="col-md-4">
                <h5 className="mb-3">Recent Activity</h5>
                <div className="list-group list-group-flush">
                  {alerts.slice(0, 3).map((alert) => (
                    <div key={alert.id} className="list-group-item border-0 px-0">
                      <div className="d-flex align-items-start">
                        <span className={getSeverityBadge(alert.severity)}>
                          {alert.severity}
                        </span>
                        <div className="ms-2 flex-grow-1">
                          <div className="fw-semibold small">{alert.title}</div>
                          <div className="text-muted small">{getTimeAgo(alert.timestamp)}</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'services' && (
            <div className="table-responsive">
              <table className="table table-hover">
                <thead>
                  <tr>
                    <th>Service</th>
                    <th>Type</th>
                    <th>Status</th>
                    <th>Uptime</th>
                    <th>Response Time</th>
                    <th>Last Check</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {services.map((service) => (
                    <tr key={service.id}>
                      <td>
                        <div className="d-flex align-items-center">
                          {getServiceIcon(service.type)}
                          <div className="ms-2">
                            <div className="fw-semibold">{service.name}</div>
                            {service.url && (
                              <div className="text-muted small">{service.url}</div>
                            )}
                          </div>
                        </div>
                      </td>
                      <td>
                        <span className="badge bg-light text-dark">
                          {service.type}
                        </span>
                      </td>
                      <td>
                        <span className={getStatusBadge(service.status)}>
                          {getStatusIcon(service.status)}
                          <span className="ms-1">{service.status}</span>
                        </span>
                      </td>
                      <td>{formatUptime(service.uptime)}</td>
                      <td>
                        {service.responseTime > 0 ? `${service.responseTime}ms` : '-'}
                      </td>
                      <td>
                        <div className="small">
                          {getTimeAgo(service.lastCheck)}
                        </div>
                      </td>
                      <td>
                        <div className="btn-group btn-group-sm">
                          <button className="btn btn-outline-primary">
                            <Activity size={12} />
                          </button>
                          <button className="btn btn-outline-secondary">
                            <Monitor size={12} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === 'alerts' && (
            <div>
              <div className="d-flex justify-content-between align-items-center mb-3">
                <h5 className="mb-0">System Alerts</h5>
                <button className="btn btn-sm btn-outline-primary">
                  Acknowledge All
                </button>
              </div>
              <div className="list-group">
                {alerts.map((alert) => (
                  <div 
                    key={alert.id} 
                    className={`list-group-item ${alert.acknowledged ? 'opacity-75' : ''}`}
                  >
                    <div className="d-flex align-items-start justify-content-between">
                      <div className="d-flex align-items-start">
                        <span className={getSeverityBadge(alert.severity)}>
                          {alert.severity}
                        </span>
                        <div className="ms-3">
                          <div className="fw-semibold">{alert.title}</div>
                          <div className="text-muted mb-1">{alert.message}</div>
                          <div className="small text-muted">
                            {alert.source} • {formatDateTime(alert.timestamp)}
                          </div>
                        </div>
                      </div>
                      <div className="d-flex align-items-center">
                        {alert.acknowledged && (
                          <span className="badge bg-success me-2">Acknowledged</span>
                        )}
                        {!alert.acknowledged && (
                          <button className="btn btn-sm btn-outline-primary">
                            Acknowledge
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default InfrastructureMonitoring;