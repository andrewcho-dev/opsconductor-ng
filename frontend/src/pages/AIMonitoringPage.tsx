import React, { useState, useEffect } from 'react';
import { 
  Brain, Activity, AlertTriangle, CheckCircle, Clock, 
  Zap, Database, RefreshCw, TrendingUp, BarChart3
} from 'lucide-react';
import { aiApi } from '../services/api';

interface AIMonitoringData {
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

const AIMonitoringPage: React.FC = () => {
  const [monitoringData, setMonitoringData] = useState<AIMonitoringData | null>(null);
  const [knowledgeStats, setKnowledgeStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  useEffect(() => {
    loadMonitoringData();
    loadKnowledgeStats();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      loadMonitoringData();
      loadKnowledgeStats();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const loadMonitoringData = async () => {
    try {
      const data = await aiApi.monitoringDashboard();
      setMonitoringData(data);
      setLastUpdated(new Date());
    } catch (err: any) {
      setError(err.message || 'Failed to load monitoring data');
    } finally {
      setLoading(false);
    }
  };

  const loadKnowledgeStats = async () => {
    try {
      const stats = await aiApi.getKnowledgeStats();
      setKnowledgeStats(stats);
    } catch (err: any) {
      console.error('Failed to load knowledge stats:', err);
    }
  };

  const handleResetCircuitBreaker = async (serviceName: string) => {
    try {
      await aiApi.resetCircuitBreaker(serviceName);
      loadMonitoringData();
    } catch (err: any) {
      setError(err.message || 'Failed to reset circuit breaker');
    }
  };

  const getHealthBadge = (health: string) => {
    switch (health.toLowerCase()) {
      case 'healthy': return 'badge bg-success';
      case 'degraded': return 'badge bg-warning';
      case 'unhealthy': return 'badge bg-danger';
      default: return 'badge bg-secondary';
    }
  };

  const getHealthIcon = (health: string) => {
    switch (health.toLowerCase()) {
      case 'healthy': return <CheckCircle className="text-success" size={16} />;
      case 'degraded': return <AlertTriangle className="text-warning" size={16} />;
      case 'unhealthy': return <AlertTriangle className="text-danger" size={16} />;
      default: return <Clock className="text-secondary" size={16} />;
    }
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical': return 'badge bg-danger';
      case 'high': return 'badge bg-warning';
      case 'medium': return 'badge bg-info';
      case 'low': return 'badge bg-light text-dark';
      default: return 'badge bg-secondary';
    }
  };

  if (loading) {
    return (
      <div className="container-fluid">
        <div className="d-flex justify-content-center align-items-center" style={{ height: '400px' }}>
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container-fluid">
      <div className="row">
        <div className="col-12">
          <div className="d-flex justify-content-between align-items-center mb-4">
            <div>
              <h1 className="h3 mb-0">
                <Brain className="me-2" size={24} />
                AI Brain Monitoring
              </h1>
              <p className="text-muted mb-0">Monitor AI services health and performance</p>
            </div>
            <div className="d-flex align-items-center gap-2">
              <small className="text-muted">
                Last updated: {lastUpdated.toLocaleTimeString()}
              </small>
              <button
                className="btn btn-outline-primary btn-sm"
                onClick={() => {
                  loadMonitoringData();
                  loadKnowledgeStats();
                }}
              >
                <RefreshCw size={16} className="me-1" />
                Refresh
              </button>
            </div>
          </div>

          {error && (
            <div className="alert alert-danger alert-dismissible fade show" role="alert">
              {error}
              <button
                type="button"
                className="btn-close"
                onClick={() => setError(null)}
              ></button>
            </div>
          )}

          {/* Overall Health Status */}
          <div className="row mb-4">
            <div className="col-md-3">
              <div className="card">
                <div className="card-body text-center">
                  <div className="mb-2">
                    {getHealthIcon(monitoringData?.current.overall_health || 'unknown')}
                  </div>
                  <h6 className="card-title">Overall Health</h6>
                  <span className={getHealthBadge(monitoringData?.current.overall_health || 'unknown')}>
                    {monitoringData?.current.overall_health || 'Unknown'}
                  </span>
                </div>
              </div>
            </div>
            <div className="col-md-3">
              <div className="card">
                <div className="card-body text-center">
                  <div className="mb-2">
                    <Activity className="text-primary" size={24} />
                  </div>
                  <h6 className="card-title">Active Services</h6>
                  <h4 className="text-primary">
                    {monitoringData?.current.services ? Object.keys(monitoringData.current.services).length : 0}
                  </h4>
                </div>
              </div>
            </div>
            <div className="col-md-3">
              <div className="card">
                <div className="card-body text-center">
                  <div className="mb-2">
                    <AlertTriangle className="text-warning" size={24} />
                  </div>
                  <h6 className="card-title">Active Alerts</h6>
                  <h4 className="text-warning">
                    {monitoringData?.analysis.alerts.length || 0}
                  </h4>
                </div>
              </div>
            </div>
            <div className="col-md-3">
              <div className="card">
                <div className="card-body text-center">
                  <div className="mb-2">
                    <Database className="text-info" size={24} />
                  </div>
                  <h6 className="card-title">Knowledge Items</h6>
                  <h4 className="text-info">
                    {knowledgeStats?.total_documents || 0}
                  </h4>
                </div>
              </div>
            </div>
          </div>

          {/* Service Status */}
          <div className="row mb-4">
            <div className="col-12">
              <div className="card">
                <div className="card-header">
                  <h6 className="card-title mb-0">Service Status</h6>
                </div>
                <div className="card-body">
                  {monitoringData?.current.services ? (
                    <div className="row">
                      {Object.entries(monitoringData.current.services).map(([serviceName, serviceData]: [string, any]) => (
                        <div key={serviceName} className="col-md-6 col-lg-4 mb-3">
                          <div className="card border">
                            <div className="card-body">
                              <div className="d-flex justify-content-between align-items-start mb-2">
                                <h6 className="card-title text-capitalize">{serviceName.replace('_', ' ')}</h6>
                                {getHealthIcon(serviceData.status || 'unknown')}
                              </div>
                              <div className="mb-2">
                                <span className={getHealthBadge(serviceData.status || 'unknown')}>
                                  {serviceData.status || 'Unknown'}
                                </span>
                              </div>
                              {serviceData.response_time && (
                                <div className="small text-muted mb-2">
                                  Response: {serviceData.response_time}ms
                                </div>
                              )}
                              {serviceData.circuit_breaker_state && (
                                <div className="d-flex justify-content-between align-items-center">
                                  <span className="small">
                                    Circuit: {serviceData.circuit_breaker_state}
                                  </span>
                                  {serviceData.circuit_breaker_state === 'open' && (
                                    <button
                                      className="btn btn-outline-warning btn-sm"
                                      onClick={() => handleResetCircuitBreaker(serviceName)}
                                    >
                                      <Zap size={12} className="me-1" />
                                      Reset
                                    </button>
                                  )}
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-muted">No service data available</p>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Alerts and Recommendations */}
          <div className="row mb-4">
            <div className="col-md-6">
              <div className="card">
                <div className="card-header">
                  <h6 className="card-title mb-0">Active Alerts</h6>
                </div>
                <div className="card-body">
                  {monitoringData?.analysis.alerts && monitoringData.analysis.alerts.length > 0 ? (
                    <div className="list-group list-group-flush">
                      {monitoringData.analysis.alerts.map((alert, index) => (
                        <div key={index} className="list-group-item px-0">
                          <div className="d-flex justify-content-between align-items-start">
                            <div>
                              <div className="fw-medium">{alert.service}</div>
                              <div className="text-muted small">{alert.message}</div>
                            </div>
                            <span className={getSeverityBadge(alert.severity)}>
                              {alert.severity}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-3">
                      <CheckCircle className="text-success mb-2" size={32} />
                      <p className="text-muted mb-0">No active alerts</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
            <div className="col-md-6">
              <div className="card">
                <div className="card-header">
                  <h6 className="card-title mb-0">Recommendations</h6>
                </div>
                <div className="card-body">
                  {monitoringData?.analysis.recommendations && monitoringData.analysis.recommendations.length > 0 ? (
                    <ul className="list-unstyled mb-0">
                      {monitoringData.analysis.recommendations.map((recommendation, index) => (
                        <li key={index} className="mb-2">
                          <div className="d-flex align-items-start">
                            <TrendingUp className="text-info me-2 mt-1" size={16} />
                            <span className="small">{recommendation}</span>
                          </div>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <div className="text-center py-3">
                      <CheckCircle className="text-success mb-2" size={32} />
                      <p className="text-muted mb-0">No recommendations at this time</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Knowledge Base Statistics */}
          {knowledgeStats && (
            <div className="row mb-4">
              <div className="col-12">
                <div className="card">
                  <div className="card-header">
                    <h6 className="card-title mb-0">Knowledge Base Statistics</h6>
                  </div>
                  <div className="card-body">
                    <div className="row">
                      <div className="col-md-3">
                        <div className="text-center">
                          <div className="h4 text-primary">{knowledgeStats.total_documents || 0}</div>
                          <div className="small text-muted">Total Documents</div>
                        </div>
                      </div>
                      <div className="col-md-3">
                        <div className="text-center">
                          <div className="h4 text-success">{knowledgeStats.total_embeddings || 0}</div>
                          <div className="small text-muted">Embeddings</div>
                        </div>
                      </div>
                      <div className="col-md-3">
                        <div className="text-center">
                          <div className="h4 text-info">{knowledgeStats.collections_count || 0}</div>
                          <div className="small text-muted">Collections</div>
                        </div>
                      </div>
                      <div className="col-md-3">
                        <div className="text-center">
                          <div className="h4 text-warning">
                            {knowledgeStats.last_updated ? 
                              new Date(knowledgeStats.last_updated).toLocaleDateString() : 
                              'Never'
                            }
                          </div>
                          <div className="small text-muted">Last Updated</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Performance Statistics */}
          {monitoringData?.statistics && (
            <div className="row">
              <div className="col-12">
                <div className="card">
                  <div className="card-header">
                    <h6 className="card-title mb-0">Performance Statistics</h6>
                  </div>
                  <div className="card-body">
                    <div className="row">
                      {Object.entries(monitoringData.statistics).map(([key, value]: [string, any]) => (
                        <div key={key} className="col-md-3 mb-3">
                          <div className="text-center">
                            <div className="d-flex align-items-center justify-content-center mb-2">
                              <BarChart3 className="text-primary me-2" size={20} />
                              <span className="fw-medium text-capitalize">
                                {key.replace('_', ' ')}
                              </span>
                            </div>
                            <div className="h5 text-primary">
                              {typeof value === 'number' ? value.toLocaleString() : value}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AIMonitoringPage;