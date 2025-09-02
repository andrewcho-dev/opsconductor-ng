import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { targetApi, credentialApi } from '../services/api';
import { enhancedTargetApi, targetServiceApi, targetCredentialApi } from '../services/enhancedApi';
import { Target, TargetCreate, Credential } from '../types';
import { EnhancedTarget, TargetService, TargetCredential } from '../types/enhanced';

const Targets: React.FC = () => {
  const navigate = useNavigate();
  const { action, id } = useParams<{ action?: string; id?: string }>();
  const [targets, setTargets] = useState<EnhancedTarget[]>([]);
  const [credentials, setCredentials] = useState<Credential[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testingTarget, setTestingTarget] = useState<number | null>(null);
  const [selectedTarget, setSelectedTarget] = useState<EnhancedTarget | null>(null);
  const [showDetailPanel, setShowDetailPanel] = useState(false);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [testingService, setTestingService] = useState<number | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const [formData, setFormData] = useState<TargetCreate>({
    name: '',
    hostname: '',
    ip_address: '',
    protocol: 'winrm',
    port: 5985,
    os_type: 'windows',
    credential_ref: 0,
    tags: [],
    metadata: {},
    depends_on: []
  });

  const isEditing = action === 'edit' && id;
  const isCreating = action === 'create';
  const showForm = isEditing || isCreating;

  useEffect(() => {
    fetchTargets();
    fetchCredentials();
  }, []);

  // Add a retry mechanism for initial load
  useEffect(() => {
    if (!loading && targets.length === 0 && retryCount < 2) {
      // If we finished loading but have no targets, retry up to 2 times with increasing delay
      const delay = (retryCount + 1) * 1000; // 1s, 2s
      const timer = setTimeout(() => {
        console.log(`Retrying targets fetch (attempt ${retryCount + 1}) after initial empty result`);
        setRetryCount(prev => prev + 1);
        fetchTargets();
      }, delay);
      
      return () => clearTimeout(timer);
    }
  }, [loading, targets.length, retryCount]);

  useEffect(() => {
    if (isEditing && id) {
      const target = targets.find(t => t.id === parseInt(id));
      if (target) {
        setFormData({
          name: target.name,
          hostname: target.hostname,
          ip_address: target.ip_address || '',
          protocol: target.protocol,
          port: target.port,
          os_type: target.os_type,
          credential_ref: target.credential_ref,
          tags: target.tags || [],
          metadata: target.metadata || {},
          depends_on: target.depends_on || []
        });
      }
    } else if (isCreating) {
      setFormData({
        name: '',
        hostname: '',
        ip_address: '',
        protocol: 'winrm',
        port: 5985,
        os_type: 'windows',
        credential_ref: 0,
        tags: [],
        metadata: {},
        depends_on: []
      });
    }
  }, [isEditing, isCreating, id, targets]);

  const fetchTargets = async () => {
    try {
      console.log('Fetching targets...');
      const response = await enhancedTargetApi.list();
      console.log('Targets response:', response);
      const targetsList = response.targets || [];
      setTargets(targetsList);
      
      // Reset retry count on successful fetch
      if (targetsList.length > 0) {
        setRetryCount(0);
      }
    } catch (error) {
      console.error('Failed to fetch targets:', error);
      // Check if it's an authentication error
      if (error.response?.status === 401 || error.response?.status === 403) {
        console.log('Authentication error, targets will be empty until token refresh');
      }
      setTargets([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchCredentials = async () => {
    try {
      const response = await credentialApi.list();
      setCredentials(response.credentials || []);
    } catch (error) {
      console.error('Failed to fetch credentials:', error);
      setCredentials([]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    
    try {
      if (isEditing && id) {
        await targetApi.update(parseInt(id), formData);
      } else {
        await targetApi.create(formData);
      }
      
      await fetchTargets();
      navigate('/targets-management');
    } catch (error) {
      console.error(`Failed to ${isEditing ? 'update' : 'create'} target:`, error);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (targetId: number) => {
    if (window.confirm('Delete this target? This action cannot be undone.')) {
      try {
        await targetApi.delete(targetId);
        fetchTargets();
      } catch (error) {
        console.error('Failed to delete target:', error);
      }
    }
  };

  const handleTest = async (targetId: number) => {
    setTestingTarget(targetId);
    try {
      await targetApi.test(targetId);
      alert('Connection test successful!');
    } catch (error) {
      console.error('Connection test failed:', error);
      alert('Connection test failed. Check the logs for details.');
    } finally {
      setTestingTarget(null);
    }
  };

  const handleTargetClick = async (targetId: number) => {
    setLoadingDetails(true);
    try {
      const enhancedTarget = await enhancedTargetApi.get(targetId);
      setSelectedTarget(enhancedTarget);
      setShowDetailPanel(true);
    } catch (error) {
      console.error('Failed to fetch target details:', error);
    } finally {
      setLoadingDetails(false);
    }
  };

  const handleCloseDetailPanel = () => {
    setShowDetailPanel(false);
    setSelectedTarget(null);
  };

  const handleServiceTest = async (serviceId: number) => {
    if (!selectedTarget) return;
    
    setTestingService(serviceId);
    try {
      await targetServiceApi.testConnection(selectedTarget.id, serviceId);
      alert('Service connection test successful!');
    } catch (error) {
      console.error('Service connection test failed:', error);
      alert('Service connection test failed. Check the logs for details.');
    } finally {
      setTestingService(null);
    }
  };

  const handleProtocolChange = (protocol: string) => {
    const defaultPorts: Record<string, number> = {
      'winrm': 5985,
      'ssh': 22,
      'https': 443,
      'http': 80
    };
    
    setFormData({
      ...formData,
      protocol,
      port: defaultPorts[protocol] || 5985
    });
  };

  const getStatusBadge = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'online':
      case 'connected':
        return 'status-badge-success';
      case 'offline':
      case 'disconnected':
        return 'status-badge-danger';
      case 'partial':
        return 'status-badge-warning';
      case 'unknown':
      default:
        return 'status-badge-neutral';
    }
  };

  const getCredentialName = (credentialRef: number) => {
    const credential = credentials.find(c => c.id === credentialRef);
    return credential ? credential.name : `ID: ${credentialRef}`;
  };

  const getTargetStatus = (target: EnhancedTarget) => {
    // Compute status based on services if available
    if (target.services && target.services.length > 0) {
      const connectedServices = target.services.filter(s => s.connection_status === 'connected');
      const failedServices = target.services.filter(s => s.connection_status === 'failed');
      
      if (connectedServices.length === target.services.length) {
        return 'Online';
      } else if (failedServices.length === target.services.length) {
        return 'Offline';
      } else if (connectedServices.length > 0) {
        return 'Partial';
      }
    }
    return 'Unknown';
  };

  if (loading) {
    return (
      <div className="loading-overlay">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  if (showForm) {
    return (
      <div className="main-content">
        <div className="page-header">
          <h1 className="page-title">
            {isEditing ? 'Edit Target' : 'Create Target'}
          </h1>
          <div className="page-actions">
            <button 
              type="button" 
              className="btn btn-ghost"
              onClick={() => navigate('/targets-management')}
            >
              Cancel
            </button>
          </div>
        </div>

        <div className="form-container">
          <form onSubmit={handleSubmit}>
            <div className="form-grid">
              <div className="form-group">
                <label className="form-label">Name</label>
                <input
                  type="text"
                  className="form-input"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Hostname</label>
                <input
                  type="text"
                  className="form-input"
                  value={formData.hostname}
                  onChange={(e) => setFormData({...formData, hostname: e.target.value})}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">IP Address</label>
                <input
                  type="text"
                  className="form-input"
                  value={formData.ip_address}
                  onChange={(e) => setFormData({...formData, ip_address: e.target.value})}
                  placeholder="Optional"
                />
              </div>

              <div className="form-group">
                <label className="form-label">OS Type</label>
                <select 
                  className="form-select"
                  value={formData.os_type}
                  onChange={(e) => setFormData({...formData, os_type: e.target.value})}
                >
                  <option value="windows">Windows</option>
                  <option value="linux">Linux</option>
                  <option value="macos">macOS</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Protocol</label>
                <select 
                  className="form-select"
                  value={formData.protocol}
                  onChange={(e) => handleProtocolChange(e.target.value)}
                >
                  <option value="winrm">WinRM</option>
                  <option value="ssh">SSH</option>
                  <option value="https">HTTPS</option>
                  <option value="http">HTTP</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Port</label>
                <input
                  type="number"
                  className="form-input"
                  value={formData.port}
                  onChange={(e) => setFormData({...formData, port: parseInt(e.target.value)})}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Credential</label>
                <select 
                  className="form-select"
                  value={formData.credential_ref}
                  onChange={(e) => setFormData({...formData, credential_ref: parseInt(e.target.value)})}
                  required
                >
                  <option value={0}>Select a credential</option>
                  {credentials.map(credential => (
                    <option key={credential.id} value={credential.id}>
                      {credential.name} ({credential.credential_type.toUpperCase()})
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                <label className="form-label">Tags (comma-separated)</label>
                <input
                  type="text"
                  className="form-input"
                  value={formData.tags?.join(', ') || ''}
                  onChange={(e) => setFormData({
                    ...formData, 
                    tags: e.target.value.split(',').map(tag => tag.trim()).filter(tag => tag)
                  })}
                  placeholder="production, web-server, critical"
                />
              </div>
            </div>

            <div className="form-actions">
              <button 
                type="button" 
                className="btn btn-ghost"
                onClick={() => navigate('/targets-management')}
              >
                Cancel
              </button>
              <button 
                type="submit" 
                className="btn btn-primary"
                disabled={saving}
              >
                {saving ? (
                  <>
                    <span className="loading-spinner"></span>
                    {isEditing ? 'Updating...' : 'Creating...'}
                  </>
                ) : (
                  isEditing ? 'Update Target' : 'Create Target'
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="main-content">
      <style>
        {`
          .targets-table {
            table-layout: auto;
            width: auto;
          }
          .targets-table th:nth-child(1), .targets-table td:nth-child(1) { min-width: 160px; max-width: 200px; } /* Name */
          .targets-table th:nth-child(2), .targets-table td:nth-child(2) { min-width: 120px; max-width: 140px; } /* IP */
          .targets-table th:nth-child(3), .targets-table td:nth-child(3) { min-width: 180px; max-width: 250px; } /* Hostname */
          .targets-table th:nth-child(4), .targets-table td:nth-child(4) { min-width: 80px; max-width: 120px; } /* OS */
          .targets-table th:nth-child(5), .targets-table td:nth-child(5) { min-width: 80px; max-width: 100px; } /* Status */
          .targets-table th:nth-child(6), .targets-table td:nth-child(6) { min-width: 150px; max-width: 250px; } /* Tags */
          .targets-table th:nth-child(7), .targets-table td:nth-child(7) { min-width: 80px; max-width: 100px; } /* Actions */
          .targets-table td {
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            padding: 8px 12px;
          }
          .targets-table th {
            padding: 8px 12px;
          }
          .targets-table td.tags-cell {
            white-space: normal;
            word-wrap: break-word;
            line-height: 1.4;
          }
        `}
      </style>
      <div className="page-header">
        <h1 className="page-title">Targets</h1>
        <div className="page-actions">
          <button 
            className="btn btn-primary"
            onClick={() => navigate('/targets-management/create')}
          >
            <span className="icon-add"></span>
            Add Target
          </button>
        </div>
      </div>

      {targets.length === 0 ? (
        <div className="empty-state">
          <h3 className="empty-state-title">No targets found</h3>
          <p className="empty-state-description">
            Create your first target to start managing remote systems.
          </p>
          <button 
            className="btn btn-primary"
            onClick={() => navigate('/targets-management/create')}
          >
            <span className="icon-add"></span>
            Create Target
          </button>
        </div>
      ) : (
        <div className={`data-table-container ${showDetailPanel ? 'with-detail-panel' : ''}`}>
          <table className="data-table targets-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>IP</th>
                <th>Hostname</th>
                <th>OS</th>
                <th>Status</th>
                <th>Tags</th>
                <th className="text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {targets.map(target => (
                <tr 
                  key={target.id}
                  className={`clickable-row ${selectedTarget?.id === target.id ? 'selected' : ''}`}
                  onClick={() => handleTargetClick(target.id)}
                >
                  <td className="font-medium">{target.name}</td>
                  <td className="text-neutral-600">{target.ip_address || '-'}</td>
                  <td>{target.hostname}</td>
                  <td className="text-neutral-600">{target.os_type}</td>
                  <td>
                    <span className={`status-badge ${getStatusBadge(getTargetStatus(target))}`}>
                      {getTargetStatus(target)}
                    </span>
                  </td>
                  <td className="text-neutral-500 tags-cell">
                    {target.tags?.length ? target.tags.join(', ') : '-'}
                  </td>
                  <td onClick={(e) => e.stopPropagation()}>
                    <div className="table-actions">
                      <button 
                        className="btn-icon btn-danger"
                        onClick={() => handleDelete(target.id)}
                        title="Delete target"
                      >
                        <span className="icon-delete"></span>
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showDetailPanel && (
          <div className="detail-panel-overlay">
            <div className="detail-panel">
              <div className="detail-panel-header">
                <h2 className="detail-panel-title">
                  {selectedTarget?.name || 'Target Details'}
                </h2>
                <button 
                  className="btn-icon btn-ghost"
                  onClick={handleCloseDetailPanel}
                  title="Close details"
                >
                  <span className="icon-close">×</span>
                </button>
              </div>

              {loadingDetails ? (
                <div className="detail-panel-loading">
                  <div className="loading-spinner"></div>
                  <p>Loading target details...</p>
                </div>
              ) : selectedTarget ? (
                <div className="detail-panel-content">
                  {/* Target Information Section */}
                  <div className="detail-section">
                    <h3 className="detail-section-title">Target Information</h3>
                    <div className="detail-grid">
                      <div className="detail-item">
                        <label>Name</label>
                        <div className="detail-value">{selectedTarget.name}</div>
                      </div>
                      <div className="detail-item">
                        <label>Hostname</label>
                        <div className="detail-value">{selectedTarget.hostname}</div>
                      </div>
                      <div className="detail-item">
                        <label>IP Address</label>
                        <div className="detail-value">{selectedTarget.ip_address || '-'}</div>
                      </div>
                      <div className="detail-item">
                        <label>OS Type</label>
                        <div className="detail-value">{selectedTarget.os_type || '-'}</div>
                      </div>
                      <div className="detail-item">
                        <label>OS Version</label>
                        <div className="detail-value">{selectedTarget.os_version || '-'}</div>
                      </div>
                      <div className="detail-item">
                        <label>Description</label>
                        <div className="detail-value">{selectedTarget.description || '-'}</div>
                      </div>
                      <div className="detail-item detail-item-full">
                        <label>Tags</label>
                        <div className="detail-value">
                          {selectedTarget.tags?.length ? (
                            <div className="tag-list">
                              {selectedTarget.tags.map((tag, index) => (
                                <span key={index} className="tag">{tag}</span>
                              ))}
                            </div>
                          ) : '-'}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Services Section */}
                  <div className="detail-section">
                    <h3 className="detail-section-title">
                      Services ({selectedTarget.services?.length || 0})
                    </h3>
                    {selectedTarget.services?.length ? (
                      <div className="services-list">
                        {selectedTarget.services.map(service => (
                          <div key={service.id} className="service-item">
                            <div className="service-info">
                              <div className="service-header">
                                <span className="service-name">{service.display_name}</span>
                                <span className={`status-badge ${service.connection_status === 'connected' ? 'status-badge-success' : 
                                  service.connection_status === 'failed' ? 'status-badge-danger' : 'status-badge-neutral'}`}>
                                  {service.connection_status}
                                </span>
                              </div>
                              <div className="service-details">
                                <span className="service-type">{service.service_type}</span>
                                <span className="service-port">Port: {service.port}</span>
                                <span className="service-category">{service.category}</span>
                              </div>
                              {service.notes && (
                                <div className="service-notes">{service.notes}</div>
                              )}
                            </div>
                            <div className="service-actions">
                              <button 
                                className="btn-icon btn-ghost"
                                onClick={() => handleServiceTest(service.id)}
                                disabled={testingService === service.id}
                                title="Test service connection"
                              >
                                {testingService === service.id ? (
                                  <span className="loading-spinner"></span>
                                ) : (
                                  <span className="icon-test">🔍</span>
                                )}
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="empty-state-small">
                        <p>No services configured for this target.</p>
                      </div>
                    )}
                  </div>

                  {/* Credentials Section */}
                  <div className="detail-section">
                    <h3 className="detail-section-title">
                      Credentials ({selectedTarget.credentials?.length || 0})
                    </h3>
                    {selectedTarget.credentials?.length ? (
                      <div className="credentials-list">
                        {selectedTarget.credentials.map(credential => (
                          <div key={credential.id} className="credential-item">
                            <div className="credential-info">
                              <div className="credential-header">
                                <span className="credential-name">{credential.credential_name}</span>
                                {credential.is_primary && (
                                  <span className="status-badge status-badge-success">Primary</span>
                                )}
                              </div>
                              <div className="credential-details">
                                <span className="credential-type">{credential.credential_type}</span>
                                {credential.service_types?.length && (
                                  <span className="credential-services">
                                    Services: {credential.service_types.join(', ')}
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="empty-state-small">
                        <p>No credentials configured for this target.</p>
                      </div>
                    )}
                  </div>
                </div>
              ) : null}
            </div>
          </div>
        )}
    </div>
  );
};

export default Targets;