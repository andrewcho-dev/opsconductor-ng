import React, { useState, useEffect } from 'react';
import { 
  enhancedTargetApi, 
  serviceDefinitionApi, 
  targetServiceApi, 
  targetCredentialApi
} from '../services/enhancedApi';
import { credentialApi } from '../services/api';
import {
  EnhancedTarget,
  EnhancedTargetCreate,
  ServiceDefinition,
  TargetService,
  TargetCredential,
  ServiceFormData,
  CredentialFormData,
  SERVICE_CATEGORIES
} from '../types/enhanced';
import { Credential } from '../types';
import { Plus } from 'lucide-react';

const EnhancedTargetManagement: React.FC = () => {
  // State management
  const [targets, setTargets] = useState<EnhancedTarget[]>([]);
  const [serviceDefinitions, setServiceDefinitions] = useState<ServiceDefinition[]>([]);
  const [credentials, setCredentials] = useState<Credential[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal states
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showServiceModal, setShowServiceModal] = useState(false);
  const [showCredentialModal, setShowCredentialModal] = useState(false);
  const [editingTarget, setEditingTarget] = useState<EnhancedTarget | null>(null);
  const [selectedTarget, setSelectedTarget] = useState<EnhancedTarget | null>(null);

  // Form data
  const [targetFormData, setTargetFormData] = useState<EnhancedTargetCreate>({
    name: '',
    hostname: '',
    ip_address: '',
    os_type: 'windows',
    os_version: '',
    description: '',
    tags: [],
    services: [],
    credentials: []
  });

  const [serviceFormData, setServiceFormData] = useState<ServiceFormData>({
    service_type: '',
    port: 0,
    is_secure: false,
    is_enabled: true,
    notes: ''
  });

  const [credentialFormData, setCredentialFormData] = useState<CredentialFormData>({
    credential_id: 0,
    service_types: [],
    is_primary: false
  });

  // Filters and UI state
  const [filters, setFilters] = useState({
    os_type: '',
    service_type: '',
    category: ''
  });
  const [expandedTargets, setExpandedTargets] = useState<Set<number>>(new Set());

  // Load data on component mount
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [targetsResponse, servicesResponse, credentialsResponse] = await Promise.all([
        enhancedTargetApi.list(),
        serviceDefinitionApi.list(),
        credentialApi.list()
      ]);

      const loadedTargets = targetsResponse.targets || [];
      setTargets(loadedTargets);
      setServiceDefinitions(servicesResponse.services || []);
      setCredentials(credentialsResponse.credentials || []);
      
      // Expand all targets by default to show CRUD buttons
      const allTargetIds = new Set(loadedTargets.map(t => t.id));
      setExpandedTargets(allTargetIds);
    } catch (err: any) {
      console.error('Failed to load data:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  // Target CRUD operations
  const handleCreateTarget = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingTarget) {
        await enhancedTargetApi.update(editingTarget.id, targetFormData);
      } else {
        await enhancedTargetApi.create(targetFormData);
      }
      setShowCreateModal(false);
      resetTargetForm();
      loadData();
    } catch (err: any) {
      console.error('Failed to save target:', err);
      setError(err.response?.data?.detail || 'Failed to save target');
    }
  };

  const handleDeleteTarget = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this target? This will also remove all associated services and credentials.')) {
      try {
        await enhancedTargetApi.delete(id);
        loadData();
      } catch (err: any) {
        console.error('Failed to delete target:', err);
        setError(err.response?.data?.detail || 'Failed to delete target');
      }
    }
  };

  // Service management
  const handleAddService = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTarget) return;

    try {
      await targetServiceApi.add(selectedTarget.id, {
        service_type: serviceFormData.service_type,
        port: serviceFormData.port,
        is_secure: serviceFormData.is_secure,
        is_enabled: serviceFormData.is_enabled,
        notes: serviceFormData.notes || undefined
      });
      setShowServiceModal(false);
      resetServiceForm();
      loadData();
    } catch (err: any) {
      console.error('Failed to add service:', err);
      setError(err.response?.data?.detail || 'Failed to add service');
    }
  };

  const handleDeleteService = async (targetId: number, serviceId: number) => {
    if (window.confirm('Are you sure you want to remove this service?')) {
      try {
        await targetServiceApi.delete(targetId, serviceId);
        loadData();
      } catch (err: any) {
        console.error('Failed to delete service:', err);
        setError(err.response?.data?.detail || 'Failed to delete service');
      }
    }
  };

  const handleTestService = async (targetId: number, serviceId: number) => {
    try {
      const result = await targetServiceApi.testConnection(targetId, serviceId);
      alert(`Connection test result: ${JSON.stringify(result, null, 2)}`);
    } catch (err: any) {
      console.error('Failed to test service:', err);
      alert(`Test failed: ${err.response?.data?.detail || err.message}`);
    }
  };

  // Credential management
  const handleAddCredential = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTarget) return;

    try {
      await targetCredentialApi.add(selectedTarget.id, credentialFormData);
      setShowCredentialModal(false);
      resetCredentialForm();
      loadData();
    } catch (err: any) {
      console.error('Failed to add credential:', err);
      setError(err.response?.data?.detail || 'Failed to add credential');
    }
  };

  const handleDeleteCredential = async (targetId: number, credentialId: number) => {
    if (window.confirm('Are you sure you want to remove this credential association?')) {
      try {
        await targetCredentialApi.delete(targetId, credentialId);
        loadData();
      } catch (err: any) {
        console.error('Failed to delete credential:', err);
        setError(err.response?.data?.detail || 'Failed to delete credential');
      }
    }
  };

  // Form reset functions
  const resetTargetForm = () => {
    setTargetFormData({
      name: '',
      hostname: '',
      ip_address: '',
      os_type: 'windows',
      os_version: '',
      description: '',
      tags: [],
      services: [],
      credentials: []
    });
    setEditingTarget(null);
  };

  const resetServiceForm = () => {
    setServiceFormData({
      service_type: '',
      port: 0,
      is_secure: false,
      is_enabled: true,
      notes: ''
    });
  };

  const resetCredentialForm = () => {
    setCredentialFormData({
      credential_id: 0,
      service_types: [],
      is_primary: false
    });
  };

  // UI helper functions
  const toggleTargetExpansion = (targetId: number) => {
    const newExpanded = new Set(expandedTargets);
    if (newExpanded.has(targetId)) {
      newExpanded.delete(targetId);
    } else {
      newExpanded.add(targetId);
    }
    setExpandedTargets(newExpanded);
  };

  const getServiceDefinition = (serviceType: string) => {
    return serviceDefinitions.find(s => s.service_type === serviceType);
  };

  const getCredentialName = (credId: number) => {
    const cred = credentials.find(c => c.id === credId);
    return cred ? cred.name : `ID: ${credId}`;
  };

  const filteredTargets = targets.filter(target => {
    if (filters.os_type && target.os_type !== filters.os_type) return false;
    if (filters.service_type && !target.services.some(s => s.service_type === filters.service_type)) return false;
    return true;
  });

  // Handle service type selection
  const handleServiceTypeChange = (serviceType: string) => {
    const serviceDef = getServiceDefinition(serviceType);
    setServiceFormData({
      ...serviceFormData,
      service_type: serviceType,
      port: serviceDef?.default_port || 0,
      is_secure: serviceDef?.is_secure_by_default || false
    });
  };

  if (loading) {
    return (
      <div className="d-flex justify-content-center align-items-center" style={{ height: '400px' }}>
        <div className="spinner-border" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="container-fluid">
      {error && (
        <div className="alert alert-danger alert-dismissible fade show" role="alert">
          {error}
          <button type="button" className="btn-close" onClick={() => setError(null)}></button>
        </div>
      )}

      {/* Debug Info */}
      <div className="alert alert-info mb-3">
        <strong>Debug Info:</strong> Loaded {targets.length} targets, {serviceDefinitions.length} service definitions, {credentials.length} credentials
      </div>

      {/* Header */}
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h1>Enhanced Target Management</h1>
        <button 
          className="btn btn-primary"
          onClick={() => {
            resetTargetForm();
            setShowCreateModal(true);
          }}
        >
          <Plus size={16} className="me-2" />Add Target
        </button>
      </div>

      {/* Filters */}
      <div className="card mb-4">
        <div className="card-body">
          <div className="row g-3">
            <div className="col-md-3">
              <label className="form-label">OS Type</label>
              <select 
                className="form-select"
                value={filters.os_type}
                onChange={(e) => setFilters({...filters, os_type: e.target.value})}
              >
                <option value="">All OS Types</option>
                <option value="windows">Windows</option>
                <option value="linux">Linux</option>
                <option value="unix">Unix</option>
                <option value="macos">macOS</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div className="col-md-3">
              <label className="form-label">Service Type</label>
              <select 
                className="form-select"
                value={filters.service_type}
                onChange={(e) => setFilters({...filters, service_type: e.target.value})}
              >
                <option value="">All Services</option>
                {serviceDefinitions.map(service => (
                  <option key={service.service_type} value={service.service_type}>
                    {service.display_name}
                  </option>
                ))}
              </select>
            </div>
            <div className="col-md-3">
              <label className="form-label">Actions</label>
              <div>
                <button 
                  className="btn btn-outline-secondary me-2"
                  onClick={() => setFilters({ os_type: '', service_type: '', category: '' })}
                >
                  Clear Filters
                </button>
                <button 
                  className="btn btn-outline-primary"
                  onClick={loadData}
                >
                  <i className="fas fa-sync-alt me-1"></i>Refresh
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Targets List */}
      <div className="row">
        <div className="col-12 mb-3">
          <div className="alert alert-warning">
            <strong>Filter Debug:</strong> Showing {filteredTargets.length} of {targets.length} targets
            {filteredTargets.length > 0 && (
              <div>Target names: {filteredTargets.map(t => t.name).join(', ')}</div>
            )}
          </div>
        </div>
        {filteredTargets.length === 0 ? (
          <div className="col-12">
            <div className="card">
              <div className="card-body text-center py-5">
                <i className="fas fa-server fa-3x text-muted mb-3"></i>
                <h5>No targets found</h5>
                <p className="text-muted">Create your first target to get started.</p>
              </div>
            </div>
          </div>
        ) : (
          filteredTargets.map(target => (
            <div key={target.id} className="col-12 mb-3">
              <div className="card">
                <div className="card-header">
                  <div className="d-flex justify-content-between align-items-center">
                    <div className="d-flex align-items-center">
                      <button
                        className="btn btn-sm btn-outline-secondary me-3"
                        onClick={() => toggleTargetExpansion(target.id)}
                      >
                        <i className={`fas fa-chevron-${expandedTargets.has(target.id) ? 'down' : 'right'}`}></i>
                      </button>
                      <div>
                        <h5 className="mb-1">{target.name}</h5>
                        <small className="text-muted">
                          {target.hostname} {target.ip_address && `(${target.ip_address})`}
                          {target.os_type && (
                            <span className="badge bg-secondary ms-2">{target.os_type}</span>
                          )}
                        </small>
                      </div>
                    </div>
                    <div>
                      <span className="badge bg-info me-2">
                        {target.services.length} service{target.services.length !== 1 ? 's' : ''}
                      </span>
                      <span className="badge bg-success me-2">
                        {target.credentials.length} credential{target.credentials.length !== 1 ? 's' : ''}
                      </span>
                      <div className="btn-group">
                        <button
                          className="btn btn-primary"
                          onClick={() => {
                            setEditingTarget(target);
                            setTargetFormData({
                              name: target.name,
                              hostname: target.hostname,
                              ip_address: target.ip_address || '',
                              os_type: target.os_type as any || 'windows',
                              os_version: target.os_version || '',
                              description: target.description || '',
                              tags: target.tags || []
                            });
                            setShowCreateModal(true);
                          }}
                          title="Edit Target"
                        >
                          <i className="fas fa-edit me-1"></i>Edit
                        </button>
                        <button
                          className="btn btn-danger ms-2"
                          onClick={() => handleDeleteTarget(target.id)}
                          title="Delete Target"
                        >
                          <i className="fas fa-trash me-1"></i>Delete
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                {expandedTargets.has(target.id) && (
                  <div className="card-body">
                    {/* Target Details */}
                    <div className="row mb-4">
                      <div className="col-md-6">
                        <h6>Target Information</h6>
                        <table className="table table-sm">
                          <tbody>
                            <tr>
                              <td><strong>Hostname:</strong></td>
                              <td>{target.hostname}</td>
                            </tr>
                            {target.ip_address && (
                              <tr>
                                <td><strong>IP Address:</strong></td>
                                <td>{target.ip_address}</td>
                              </tr>
                            )}
                            {target.os_type && (
                              <tr>
                                <td><strong>OS Type:</strong></td>
                                <td>{target.os_type}</td>
                              </tr>
                            )}
                            {target.os_version && (
                              <tr>
                                <td><strong>OS Version:</strong></td>
                                <td>{target.os_version}</td>
                              </tr>
                            )}
                            {target.description && (
                              <tr>
                                <td><strong>Description:</strong></td>
                                <td>{target.description}</td>
                              </tr>
                            )}
                          </tbody>
                        </table>
                      </div>
                      <div className="col-md-6">
                        <h6>Tags</h6>
                        <div>
                          {target.tags.length > 0 ? (
                            target.tags.map(tag => (
                              <span key={tag} className="badge bg-light text-dark me-1 mb-1">{tag}</span>
                            ))
                          ) : (
                            <span className="text-muted">No tags</span>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Services Section */}
                    <div className="mb-4">
                      <div className="d-flex justify-content-between align-items-center mb-3">
                        <h6>Services ({target.services.length})</h6>
                        <button
                          className="btn btn-sm btn-outline-primary"
                          onClick={() => {
                            setSelectedTarget(target);
                            resetServiceForm();
                            setShowServiceModal(true);
                          }}
                        >
                          <i className="fas fa-plus me-1"></i>Add Service
                        </button>
                      </div>
                      
                      {target.services.length > 0 ? (
                        <div className="table-responsive">
                          <table className="table table-sm">
                            <thead>
                              <tr>
                                <th>Service</th>
                                <th>Category</th>
                                <th>Port</th>
                                <th>Secure</th>
                                <th>Status</th>
                                <th>Actions</th>
                              </tr>
                            </thead>
                            <tbody>
                              {target.services.map(service => (
                                <tr key={service.id}>
                                  <td>
                                    <strong>{service.display_name}</strong>
                                    {service.is_custom_port && (
                                      <span className="badge bg-warning ms-1">Custom Port</span>
                                    )}
                                  </td>
                                  <td>
                                    <span className="badge bg-secondary">{service.category}</span>
                                  </td>
                                  <td>{service.port}</td>
                                  <td>
                                    {service.is_secure ? (
                                      <i className="fas fa-lock text-success"></i>
                                    ) : (
                                      <i className="fas fa-unlock text-warning"></i>
                                    )}
                                  </td>
                                  <td>
                                    <span className={`badge ${
                                      service.is_enabled ? 'bg-success' : 'bg-secondary'
                                    }`}>
                                      {service.is_enabled ? 'Enabled' : 'Disabled'}
                                    </span>
                                  </td>
                                  <td>
                                    <div className="btn-group">
                                      <button
                                        className="btn btn-sm btn-outline-info"
                                        onClick={() => handleTestService(target.id, service.id)}
                                        title="Test Connection"
                                      >
                                        <i className="fas fa-plug"></i>
                                      </button>
                                      <button
                                        className="btn btn-sm btn-outline-danger"
                                        onClick={() => handleDeleteService(target.id, service.id)}
                                        title="Remove Service"
                                      >
                                        <i className="fas fa-trash"></i>
                                      </button>
                                    </div>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      ) : (
                        <div className="text-center py-3 text-muted">
                          <i className="fas fa-cogs fa-2x mb-2"></i>
                          <p>No services configured</p>
                        </div>
                      )}
                    </div>

                    {/* Credentials Section */}
                    <div>
                      <div className="d-flex justify-content-between align-items-center mb-3">
                        <h6>Credentials ({target.credentials.length})</h6>
                        <button
                          className="btn btn-sm btn-outline-primary"
                          onClick={() => {
                            setSelectedTarget(target);
                            resetCredentialForm();
                            setShowCredentialModal(true);
                          }}
                        >
                          <i className="fas fa-plus me-1"></i>Add Credential
                        </button>
                      </div>
                      
                      {target.credentials.length > 0 ? (
                        <div className="table-responsive">
                          <table className="table table-sm">
                            <thead>
                              <tr>
                                <th>Credential</th>
                                <th>Type</th>
                                <th>Service Types</th>
                                <th>Primary</th>
                                <th>Actions</th>
                              </tr>
                            </thead>
                            <tbody>
                              {target.credentials.map(credential => (
                                <tr key={credential.id}>
                                  <td><strong>{credential.credential_name}</strong></td>
                                  <td>
                                    <span className="badge bg-info">{credential.credential_type}</span>
                                  </td>
                                  <td>
                                    {credential.service_types.length > 0 ? (
                                      credential.service_types.map(type => (
                                        <span key={type} className="badge bg-light text-dark me-1">{type}</span>
                                      ))
                                    ) : (
                                      <span className="text-muted">All services</span>
                                    )}
                                  </td>
                                  <td>
                                    {credential.is_primary && (
                                      <i className="fas fa-star text-warning"></i>
                                    )}
                                  </td>
                                  <td>
                                    <button
                                      className="btn btn-sm btn-outline-danger"
                                      onClick={() => handleDeleteCredential(target.id, credential.id)}
                                      title="Remove Credential"
                                    >
                                      <i className="fas fa-trash"></i>
                                    </button>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      ) : (
                        <div className="text-center py-3 text-muted">
                          <i className="fas fa-key fa-2x mb-2"></i>
                          <p>No credentials configured</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Create/Edit Target Modal */}
      {showCreateModal && (
        <div className="modal show d-block" tabIndex={-1}>
          <div className="modal-dialog modal-lg">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">
                  {editingTarget ? 'Edit Target' : 'Create New Target'}
                </h5>
                <button 
                  type="button" 
                  className="btn-close" 
                  onClick={() => setShowCreateModal(false)}
                ></button>
              </div>
              <form onSubmit={handleCreateTarget}>
                <div className="modal-body">
                  <div className="row g-3">
                    <div className="col-md-6">
                      <label className="form-label">Name *</label>
                      <input
                        type="text"
                        className="form-control"
                        value={targetFormData.name}
                        onChange={(e) => setTargetFormData({...targetFormData, name: e.target.value})}
                        required
                      />
                    </div>
                    <div className="col-md-6">
                      <label className="form-label">Hostname *</label>
                      <input
                        type="text"
                        className="form-control"
                        value={targetFormData.hostname}
                        onChange={(e) => setTargetFormData({...targetFormData, hostname: e.target.value})}
                        required
                      />
                    </div>
                    <div className="col-md-6">
                      <label className="form-label">IP Address</label>
                      <input
                        type="text"
                        className="form-control"
                        value={targetFormData.ip_address}
                        onChange={(e) => setTargetFormData({...targetFormData, ip_address: e.target.value})}
                      />
                    </div>
                    <div className="col-md-6">
                      <label className="form-label">OS Type</label>
                      <select
                        className="form-select"
                        value={targetFormData.os_type}
                        onChange={(e) => setTargetFormData({...targetFormData, os_type: e.target.value as any})}
                      >
                        <option value="windows">Windows</option>
                        <option value="linux">Linux</option>
                        <option value="unix">Unix</option>
                        <option value="macos">macOS</option>
                        <option value="other">Other</option>
                      </select>
                    </div>
                    <div className="col-md-6">
                      <label className="form-label">OS Version</label>
                      <input
                        type="text"
                        className="form-control"
                        value={targetFormData.os_version}
                        onChange={(e) => setTargetFormData({...targetFormData, os_version: e.target.value})}
                      />
                    </div>
                    <div className="col-md-6">
                      <label className="form-label">Tags (comma-separated)</label>
                      <input
                        type="text"
                        className="form-control"
                        value={targetFormData.tags?.join(', ') || ''}
                        onChange={(e) => setTargetFormData({
                          ...targetFormData, 
                          tags: e.target.value.split(',').map(t => t.trim()).filter(t => t)
                        })}
                      />
                    </div>
                    <div className="col-12">
                      <label className="form-label">Description</label>
                      <textarea
                        className="form-control"
                        rows={3}
                        value={targetFormData.description}
                        onChange={(e) => setTargetFormData({...targetFormData, description: e.target.value})}
                      />
                    </div>
                  </div>
                </div>
                <div className="modal-footer">
                  <button 
                    type="button" 
                    className="btn btn-secondary" 
                    onClick={() => setShowCreateModal(false)}
                  >
                    Cancel
                  </button>
                  <button type="submit" className="btn btn-primary">
                    {editingTarget ? 'Update Target' : 'Create Target'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Add Service Modal */}
      {showServiceModal && (
        <div className="modal show d-block" tabIndex={-1}>
          <div className="modal-dialog">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">Add Service to {selectedTarget?.name}</h5>
                <button 
                  type="button" 
                  className="btn-close" 
                  onClick={() => setShowServiceModal(false)}
                ></button>
              </div>
              <form onSubmit={handleAddService}>
                <div className="modal-body">
                  <div className="mb-3">
                    <label className="form-label">Service Type *</label>
                    <select
                      className="form-select"
                      value={serviceFormData.service_type}
                      onChange={(e) => handleServiceTypeChange(e.target.value)}
                      required
                    >
                      <option value="">Select a service...</option>
                      {Object.entries(SERVICE_CATEGORIES).map(([category, displayName]) => {
                        const categoryServices = serviceDefinitions.filter(s => s.category === category);
                        if (categoryServices.length === 0) return null;
                        
                        return (
                          <optgroup key={category} label={displayName}>
                            {categoryServices.map(service => (
                              <option key={service.service_type} value={service.service_type}>
                                {service.display_name}
                              </option>
                            ))}
                          </optgroup>
                        );
                      })}
                    </select>
                  </div>
                  <div className="mb-3">
                    <label className="form-label">Port *</label>
                    <input
                      type="number"
                      className="form-control"
                      value={serviceFormData.port}
                      onChange={(e) => setServiceFormData({...serviceFormData, port: parseInt(e.target.value) || 0})}
                      required
                      min="1"
                      max="65535"
                    />
                  </div>
                  <div className="mb-3">
                    <div className="form-check">
                      <input
                        className="form-check-input"
                        type="checkbox"
                        checked={serviceFormData.is_secure}
                        onChange={(e) => setServiceFormData({...serviceFormData, is_secure: e.target.checked})}
                      />
                      <label className="form-check-label">
                        Use secure connection (SSL/TLS)
                      </label>
                    </div>
                  </div>
                  <div className="mb-3">
                    <div className="form-check">
                      <input
                        className="form-check-input"
                        type="checkbox"
                        checked={serviceFormData.is_enabled}
                        onChange={(e) => setServiceFormData({...serviceFormData, is_enabled: e.target.checked})}
                      />
                      <label className="form-check-label">
                        Enable service
                      </label>
                    </div>
                  </div>
                  <div className="mb-3">
                    <label className="form-label">Notes</label>
                    <textarea
                      className="form-control"
                      rows={3}
                      value={serviceFormData.notes}
                      onChange={(e) => setServiceFormData({...serviceFormData, notes: e.target.value})}
                    />
                  </div>
                </div>
                <div className="modal-footer">
                  <button 
                    type="button" 
                    className="btn btn-secondary" 
                    onClick={() => setShowServiceModal(false)}
                  >
                    Cancel
                  </button>
                  <button type="submit" className="btn btn-primary">
                    Add Service
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Add Credential Modal */}
      {showCredentialModal && (
        <>
          <div className="modal-backdrop fade show"></div>
          <div className="modal show d-block" tabIndex={-1}>
            <div className="modal-dialog">
              <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">Add Credential to {selectedTarget?.name}</h5>
                <button 
                  type="button" 
                  className="btn-close" 
                  onClick={() => setShowCredentialModal(false)}
                ></button>
              </div>
              <form onSubmit={handleAddCredential}>
                <div className="modal-body">
                  <div className="mb-3">
                    <label className="form-label">Credential *</label>
                    <select
                      className="form-select"
                      value={credentialFormData.credential_id}
                      onChange={(e) => setCredentialFormData({...credentialFormData, credential_id: parseInt(e.target.value)})}
                      required
                    >
                      <option value={0}>Select a credential...</option>
                      {credentials.map(credential => (
                        <option key={credential.id} value={credential.id}>
                          {credential.name} ({credential.credential_type})
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="mb-3">
                    <label className="form-label">Service Types (leave empty for all services)</label>
                    <select
                      className="form-select"
                      multiple
                      value={credentialFormData.service_types}
                      onChange={(e) => setCredentialFormData({
                        ...credentialFormData, 
                        service_types: Array.from(e.target.selectedOptions, option => option.value)
                      })}
                    >
                      {serviceDefinitions.map(service => (
                        <option key={service.service_type} value={service.service_type}>
                          {service.display_name}
                        </option>
                      ))}
                    </select>
                    <div className="form-text">Hold Ctrl/Cmd to select multiple services</div>
                  </div>
                  <div className="mb-3">
                    <div className="form-check">
                      <input
                        className="form-check-input"
                        type="checkbox"
                        checked={credentialFormData.is_primary}
                        onChange={(e) => setCredentialFormData({...credentialFormData, is_primary: e.target.checked})}
                      />
                      <label className="form-check-label">
                        Set as primary credential for selected services
                      </label>
                    </div>
                  </div>
                </div>
                <div className="modal-footer">
                  <button 
                    type="button" 
                    className="btn btn-secondary" 
                    onClick={() => setShowCredentialModal(false)}
                  >
                    Cancel
                  </button>
                  <button type="submit" className="btn btn-primary">
                    Add Credential
                  </button>
                </div>
              </form>
              </div>
            </div>
          </div>
        </>
      )}


    </div>
  );
};

export default EnhancedTargetManagement;