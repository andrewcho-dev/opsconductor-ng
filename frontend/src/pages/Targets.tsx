import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Plus, Trash2, Check, X, Search } from 'lucide-react';
import { targetApi, credentialApi } from '../services/api';
import { enhancedTargetApi, targetServiceApi, targetCredentialApi } from '../services/enhancedApi';
import { Target, TargetCreate, Credential } from '../types';
import { EnhancedTarget, TargetService, TargetCredential } from '../types/enhanced';

interface NewTargetState {
  name: string;
  hostname: string;
  ip_address: string;
  protocol: string;
  port: number;
  os_type: string;
  credential_ref: number;
  tags: string[];
  description: string;
}

const Targets: React.FC = () => {
  const navigate = useNavigate();
  const { action, id } = useParams<{ action?: string; id?: string }>();
  const [targets, setTargets] = useState<EnhancedTarget[]>([]);
  const [credentials, setCredentials] = useState<Credential[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testingTarget, setTestingTarget] = useState<number | null>(null);
  const [testingService, setTestingService] = useState<number | null>(null);
  const [selectedTarget, setSelectedTarget] = useState<EnhancedTarget | null>(null);
  const [addingNew, setAddingNew] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const [newTarget, setNewTarget] = useState<NewTargetState>({
    name: '',
    hostname: '',
    ip_address: '',
    protocol: 'winrm',
    port: 5985,
    os_type: 'windows',
    credential_ref: 0,
    tags: [],
    description: ''
  });

  useEffect(() => {
    fetchTargets();
    fetchCredentials();
  }, []);

  // Add a retry mechanism for initial load
  useEffect(() => {
    if (!loading && targets.length === 0 && retryCount < 2) {
      const delay = (retryCount + 1) * 1000;
      const timer = setTimeout(() => {
        console.log(`Retrying targets fetch (attempt ${retryCount + 1}) after initial empty result`);
        setRetryCount(prev => prev + 1);
        fetchTargets();
      }, delay);
      
      return () => clearTimeout(timer);
    }
  }, [loading, targets.length, retryCount]);

  const fetchTargets = async () => {
    try {
      console.log('Fetching targets...');
      const response = await enhancedTargetApi.list();
      console.log('Targets response:', response);
      const targetsList = response.targets || [];
      setTargets(targetsList);
      
      if (targetsList.length > 0) {
        setRetryCount(0);
      }
    } catch (error: any) {
      console.error('Failed to fetch targets:', error);
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

  const startAddingNew = () => {
    setAddingNew(true);
  };

  const cancelAddingNew = () => {
    setAddingNew(false);
    setNewTarget({
      name: '',
      hostname: '',
      ip_address: '',
      protocol: 'winrm',
      port: 5985,
      os_type: 'windows',
      credential_ref: 0,
      tags: [],
      description: ''
    });
  };

  const saveNewTarget = async () => {
    if (!newTarget.name.trim()) {
      alert('Name is required');
      return;
    }
    if (!newTarget.hostname.trim()) {
      alert('Hostname is required');
      return;
    }
    if (newTarget.credential_ref === 0) {
      alert('Please select a credential');
      return;
    }

    try {
      setSaving(true);
      const targetToCreate: TargetCreate = {
        name: newTarget.name,
        hostname: newTarget.hostname,
        ip_address: newTarget.ip_address || '',
        protocol: newTarget.protocol,
        port: newTarget.port,
        os_type: newTarget.os_type,
        credential_ref: newTarget.credential_ref,
        tags: newTarget.tags,
        metadata: {},
        depends_on: []
      };
      
      await targetApi.create(targetToCreate);
      await fetchTargets();
      cancelAddingNew();
    } catch (error) {
      console.error('Failed to create target:', error);
      alert('Failed to create target');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (targetId: number) => {
    if (window.confirm('Delete this target? This action cannot be undone.')) {
      try {
        await targetApi.delete(targetId);
        fetchTargets();
        if (selectedTarget?.id === targetId) {
          setSelectedTarget(null);
        }
      } catch (error) {
        console.error('Failed to delete target:', error);
      }
    }
  };

  const handleTest = async (targetId: number) => {
    setTestingTarget(targetId);
    try {
      await targetApi.testWinRM(targetId);
      alert('Connection test successful!');
    } catch (error) {
      console.error('Connection test failed:', error);
      alert('Connection test failed. Check the logs for details.');
    } finally {
      setTestingTarget(null);
    }
  };

  const handleTargetClick = async (target: EnhancedTarget) => {
    try {
      const enhancedTarget = await enhancedTargetApi.get(target.id);
      setSelectedTarget(enhancedTarget);
    } catch (error) {
      console.error('Failed to fetch target details:', error);
      setSelectedTarget(target); // Fallback to basic target data
    }
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
    
    setNewTarget({
      ...newTarget,
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

  const handleNewTargetKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      saveNewTarget();
    } else if (e.key === 'Escape') {
      cancelAddingNew();
    }
  };

  if (loading) {
    return (
      <div className="loading-overlay">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  return (
    <div className="dense-dashboard">
      <style>
        {`
          /* Dashboard-style layout - EXACT MATCH */
          .dense-dashboard {
            padding: 8px 12px;
            max-width: 100%;
            font-size: 13px;
          }
          .dashboard-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid var(--neutral-200);
          }
          .header-left h1 {
            font-size: 18px;
            font-weight: 600;
            margin: 0;
            color: var(--neutral-800);
          }
          .dashboard-grid {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 12px;
            align-items: stretch;
            height: calc(100vh - 110px);
          }
          .dashboard-section {
            background: white;
            border: 1px solid var(--neutral-200);
            border-radius: 6px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            height: 100%;
          }
          .section-header {
            background: var(--neutral-50);
            padding: 8px 12px;
            font-weight: 600;
            font-size: 13px;
            color: var(--neutral-700);
            border-bottom: 1px solid var(--neutral-200);
          }
          .compact-content {
            padding: 0;
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: auto;
          }
          .table-container {
            flex: 1;
            overflow: auto;
          }
          
          /* Targets table styles */
          .targets-table-section {
            grid-column: 1 / 3;
          }
          .targets-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
          }
          .targets-table th {
            background: var(--neutral-50);
            padding: 6px 8px;
            text-align: left;
            font-weight: 600;
            color: var(--neutral-700);
            border-bottom: 1px solid var(--neutral-200);
            font-size: 11px;
          }
          .targets-table td {
            padding: 6px 8px;
            border-bottom: 1px solid var(--neutral-100);
            vertical-align: middle;
            font-size: 12px;
          }
          .targets-table tr:hover {
            background: var(--neutral-50);
          }
          .targets-table tr.selected {
            background: var(--primary-blue-light);
            border-left: 3px solid var(--primary-blue);
          }
          .targets-table tr {
            cursor: pointer;
          }
          
          /* Target details panel */
          .target-details {
            padding: 8px;
          }
          .target-details h3 {
            margin: 0 0 12px 0;
            font-size: 14px;
            font-weight: 600;
            color: var(--neutral-800);
          }
          .detail-group {
            margin-bottom: 12px;
          }
          .detail-label {
            font-size: 10px;
            font-weight: 600;
            color: var(--neutral-500);
            margin-bottom: 3px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
          }
          .detail-value {
            font-size: 12px;
            color: var(--neutral-800);
            padding: 6px 0;
            border-bottom: 1px solid var(--neutral-100);
          }
          
          /* Services and credentials sections */
          .services-section, .credentials-section {
            margin-top: 16px;
            padding-top: 16px;
            border-top: 1px solid var(--neutral-200);
          }
          .section-title {
            font-size: 12px;
            font-weight: 600;
            color: var(--neutral-700);
            margin-bottom: 8px;
          }
          .service-item, .credential-item {
            background: var(--neutral-50);
            border: 1px solid var(--neutral-200);
            border-radius: 4px;
            padding: 8px;
            margin-bottom: 6px;
          }
          .service-header, .credential-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 4px;
          }
          .service-name, .credential-name {
            font-weight: 500;
            font-size: 12px;
          }
          .service-details, .credential-details {
            font-size: 10px;
            color: var(--neutral-600);
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
          }
          .service-notes {
            font-size: 10px;
            color: var(--neutral-500);
            margin-top: 4px;
            font-style: italic;
          }
          
          /* Button styles */
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
          }
          .btn-icon:hover {
            opacity: 0.7;
          }
          .btn-icon:disabled {
            opacity: 0.3;
            cursor: not-allowed;
          }
          .btn-success {
            color: var(--success-green);
          }
          .btn-success:hover:not(:disabled) {
            color: var(--success-green-dark);
          }
          .btn-danger {
            color: var(--danger-red);
          }
          .btn-danger:hover:not(:disabled) {
            color: var(--danger-red);
          }
          .btn-ghost {
            color: var(--neutral-500);
          }
          .btn-ghost:hover:not(:disabled) {
            color: var(--neutral-700);
          }
          
          .action-buttons {
            display: flex;
            gap: 4px;
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px solid var(--neutral-200);
          }
          
          .empty-state {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 150px;
            color: var(--neutral-500);
            text-align: center;
          }
          .empty-state h3 {
            margin: 0 0 6px 0;
            font-size: 14px;
            font-weight: 600;
          }
          .empty-state p {
            margin: 0 0 12px 0;
            font-size: 12px;
          }
          
          .status-badge {
            display: inline-block;
            padding: 2px 6px;
            border-radius: 12px;
            font-size: 10px;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
          }
          .status-badge-success {
            background: var(--success-green-light);
            color: var(--success-green);
          }
          .status-badge-danger {
            background: var(--danger-red-light);
            color: var(--danger-red);
          }
          .status-badge-warning {
            background: var(--warning-yellow-light);
            color: var(--warning-yellow);
          }
          .status-badge-neutral {
            background: var(--neutral-200);
            color: var(--neutral-600);
          }
          
          .tag-list {
            display: flex;
            flex-wrap: wrap;
            gap: 4px;
          }
          .tag {
            background: var(--primary-blue-light);
            color: var(--primary-blue);
            padding: 2px 6px;
            border-radius: 12px;
            font-size: 10px;
            font-weight: 500;
          }
        `}
      </style>
      
      {/* Dashboard-style header */}
      <div className="dashboard-header">
        <div className="header-left">
          <h1>Target Management</h1>
        </div>
        <div className="header-actions">
          <button 
            className="btn-icon btn-success"
            onClick={startAddingNew}
            title="Add new target"
            disabled={addingNew}
          >
            <Plus size={16} />
          </button>
        </div>
      </div>

      {/* 3-column dashboard grid */}
      <div className="dashboard-grid">
        {/* Columns 1-2: Targets Table */}
        <div className="dashboard-section targets-table-section">
          <div className="section-header">
            Targets ({targets.length})
          </div>
          <div className="compact-content">
            {targets.length === 0 && !addingNew ? (
              <div className="empty-state">
                <h3>No targets found</h3>
                <p>Create your first target to start managing remote systems.</p>
                <button 
                  className="btn-icon btn-success"
                  onClick={startAddingNew}
                  title="Create first target"
                >
                  <Plus size={16} />
                </button>
              </div>
            ) : (
              <div className="table-container">
                <table className="targets-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Hostname</th>
                    <th>IP Address</th>
                    <th>OS</th>
                    <th>Status</th>
                    <th>Tags</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {/* New Target Row */}
                  {addingNew && (
                    <tr style={{ background: '#f0f9ff', border: '2px solid #10b981' }}>
                      <td>
                        <input
                          type="text"
                          value={newTarget.name}
                          onChange={(e) => setNewTarget({...newTarget, name: e.target.value})}
                          onKeyDown={handleNewTargetKeyPress}
                          placeholder="Target name"
                          style={{ width: '100%', border: 'none', background: 'transparent', padding: '4px' }}
                          autoFocus
                        />
                      </td>
                      <td>
                        <input
                          type="text"
                          value={newTarget.hostname}
                          onChange={(e) => setNewTarget({...newTarget, hostname: e.target.value})}
                          onKeyDown={handleNewTargetKeyPress}
                          placeholder="Hostname"
                          style={{ width: '100%', border: 'none', background: 'transparent', padding: '4px' }}
                        />
                      </td>
                      <td>
                        <input
                          type="text"
                          value={newTarget.ip_address}
                          onChange={(e) => setNewTarget({...newTarget, ip_address: e.target.value})}
                          onKeyDown={handleNewTargetKeyPress}
                          placeholder="IP (optional)"
                          style={{ width: '100%', border: 'none', background: 'transparent', padding: '4px' }}
                        />
                      </td>
                      <td>
                        <select 
                          value={newTarget.os_type} 
                          onChange={(e) => setNewTarget({...newTarget, os_type: e.target.value})}
                          style={{ width: '100%', border: 'none', background: 'transparent', padding: '4px' }}
                        >
                          <option value="windows">Windows</option>
                          <option value="linux">Linux</option>
                          <option value="macos">macOS</option>
                        </select>
                      </td>
                      <td style={{ color: '#64748b', fontSize: '12px' }}>New</td>
                      <td>
                        <input
                          type="text"
                          value={newTarget.tags.join(', ')}
                          onChange={(e) => setNewTarget({...newTarget, tags: e.target.value.split(',').map(t => t.trim()).filter(t => t)})}
                          onKeyDown={handleNewTargetKeyPress}
                          placeholder="Tags"
                          style={{ width: '100%', border: 'none', background: 'transparent', padding: '4px' }}
                        />
                      </td>
                      <td>
                        <button onClick={saveNewTarget} className="btn-icon btn-success" title="Save" disabled={saving}>
                          <Check size={16} />
                        </button>
                        <button onClick={cancelAddingNew} className="btn-icon btn-ghost" title="Cancel">
                          <X size={16} />
                        </button>
                      </td>
                    </tr>
                  )}

                  {/* Existing Targets */}
                  {targets.map((target) => (
                    <tr 
                      key={target.id} 
                      className={selectedTarget?.id === target.id ? 'selected' : ''}
                      onClick={() => handleTargetClick(target)}
                    >
                      <td style={{ fontWeight: '500' }}>{target.name}</td>
                      <td>{target.hostname}</td>
                      <td>{target.ip_address || '-'}</td>
                      <td>{target.os_type}</td>
                      <td>
                        <span className={`status-badge ${getStatusBadge(getTargetStatus(target))}`}>
                          {getTargetStatus(target)}
                        </span>
                      </td>
                      <td>{target.tags?.length ? target.tags.join(', ') : '-'}</td>
                      <td>
                        <button 
                          className="btn-icon btn-ghost"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleTest(target.id);
                          }}
                          disabled={testingTarget === target.id}
                          title="Test connection"
                        >
                          {testingTarget === target.id ? (
                            <span className="loading-spinner"></span>
                          ) : (
                            <Search size={16} />
                          )}
                        </button>
                        <button 
                          className="btn-icon btn-danger"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDelete(target.id);
                          }}
                          title="Delete target"
                        >
                          <Trash2 size={16} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Column 3: Target Details Panel */}
        <div className="dashboard-section">
          <div className="section-header">
            {selectedTarget ? `Target Details` : 'Select Target'}
          </div>
          <div className="compact-content">
            {selectedTarget ? (
              <div className="target-details">
                <h3>{selectedTarget.name}</h3>
                
                <div className="detail-group">
                  <div className="detail-label">Name</div>
                  <div className="detail-value">{selectedTarget.name}</div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">Hostname</div>
                  <div className="detail-value">{selectedTarget.hostname}</div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">IP Address</div>
                  <div className="detail-value">{selectedTarget.ip_address || '-'}</div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">OS Type</div>
                  <div className="detail-value">{selectedTarget.os_type}</div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">OS Version</div>
                  <div className="detail-value">{selectedTarget.os_version || '-'}</div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">Description</div>
                  <div className="detail-value">{selectedTarget.description || '-'}</div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">Tags</div>
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

                <div className="detail-group">
                  <div className="detail-label">Status</div>
                  <div className="detail-value">
                    <span className={`status-badge ${getStatusBadge(getTargetStatus(selectedTarget))}`}>
                      {getTargetStatus(selectedTarget)}
                    </span>
                  </div>
                </div>

                {/* Services Section */}
                {selectedTarget.services && selectedTarget.services.length > 0 && (
                  <div className="services-section">
                    <div className="section-title">Services ({selectedTarget.services.length})</div>
                    {selectedTarget.services.map(service => (
                      <div key={service.id} className="service-item">
                        <div className="service-header">
                          <span className="service-name">{service.display_name}</span>
                          <span className={`status-badge ${service.connection_status === 'connected' ? 'status-badge-success' : 
                            service.connection_status === 'failed' ? 'status-badge-danger' : 'status-badge-neutral'}`}>
                            {service.connection_status}
                          </span>
                        </div>
                        <div className="service-details">
                          <span>{service.service_type}</span>
                          <span>Port: {service.port}</span>
                          <span>{service.category}</span>
                        </div>
                        {service.notes && (
                          <div className="service-notes">{service.notes}</div>
                        )}
                        <div style={{ marginTop: '6px' }}>
                          <button 
                            className="btn-icon btn-ghost"
                            onClick={() => handleServiceTest(service.id)}
                            disabled={testingService === service.id}
                            title="Test service connection"
                          >
                            {testingService === service.id ? (
                              <span className="loading-spinner"></span>
                            ) : (
                              <Search size={14} />
                            )}
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Credentials Section */}
                {selectedTarget.credentials && selectedTarget.credentials.length > 0 && (
                  <div className="credentials-section">
                    <div className="section-title">Credentials ({selectedTarget.credentials.length})</div>
                    {selectedTarget.credentials.map(credential => (
                      <div key={credential.id} className="credential-item">
                        <div className="credential-header">
                          <span className="credential-name">{credential.credential_name}</span>
                          {credential.is_primary && (
                            <span className="status-badge status-badge-success">Primary</span>
                          )}
                        </div>
                        <div className="credential-details">
                          <span>{credential.credential_type}</span>
                          {credential.service_types?.length && (
                            <span>Services: {credential.service_types.join(', ')}</span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                <div className="action-buttons">
                  <button 
                    className="btn-icon btn-ghost"
                    onClick={() => handleTest(selectedTarget.id)}
                    disabled={testingTarget === selectedTarget.id}
                    title="Test connection"
                  >
                    {testingTarget === selectedTarget.id ? (
                      <span className="loading-spinner"></span>
                    ) : (
                      <Search size={16} />
                    )}
                  </button>
                  <button 
                    className="btn-icon btn-danger"
                    onClick={() => handleDelete(selectedTarget.id)}
                    title="Delete target"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            ) : (
              <div className="empty-state">
                <p>Select a target from the table to view details and manage services</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Additional form for new target details */}
      {addingNew && (
        <div style={{
          position: 'fixed',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          background: 'white',
          border: '1px solid var(--neutral-300)',
          borderRadius: '8px',
          padding: '16px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
          zIndex: 1000,
          minWidth: '400px'
        }}>
          <h3 style={{ margin: '0 0 16px 0', fontSize: '16px' }}>Complete Target Details</h3>
          
          <div style={{ marginBottom: '12px' }}>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', marginBottom: '4px' }}>Protocol</label>
            <select 
              value={newTarget.protocol} 
              onChange={(e) => handleProtocolChange(e.target.value)}
              style={{ width: '100%', padding: '6px', border: '1px solid var(--neutral-300)', borderRadius: '4px' }}
            >
              <option value="winrm">WinRM</option>
              <option value="ssh">SSH</option>
              <option value="https">HTTPS</option>
              <option value="http">HTTP</option>
            </select>
          </div>

          <div style={{ marginBottom: '12px' }}>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', marginBottom: '4px' }}>Port</label>
            <input
              type="number"
              value={newTarget.port}
              onChange={(e) => setNewTarget({...newTarget, port: parseInt(e.target.value) || 5985})}
              style={{ width: '100%', padding: '6px', border: '1px solid var(--neutral-300)', borderRadius: '4px' }}
            />
          </div>

          <div style={{ marginBottom: '12px' }}>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', marginBottom: '4px' }}>Credential</label>
            <select 
              value={newTarget.credential_ref} 
              onChange={(e) => setNewTarget({...newTarget, credential_ref: parseInt(e.target.value)})}
              style={{ width: '100%', padding: '6px', border: '1px solid var(--neutral-300)', borderRadius: '4px' }}
            >
              <option value={0}>Select a credential</option>
              {credentials.map(credential => (
                <option key={credential.id} value={credential.id}>
                  {credential.name} ({credential.credential_type.toUpperCase()})
                </option>
              ))}
            </select>
          </div>

          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', marginBottom: '4px' }}>Description</label>
            <textarea
              value={newTarget.description}
              onChange={(e) => setNewTarget({...newTarget, description: e.target.value})}
              style={{ width: '100%', padding: '6px', border: '1px solid var(--neutral-300)', borderRadius: '4px', minHeight: '60px', resize: 'vertical' }}
              placeholder="Optional description"
            />
          </div>

          <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
            <button 
              onClick={cancelAddingNew}
              style={{ padding: '6px 12px', border: '1px solid var(--neutral-300)', background: 'white', borderRadius: '4px', cursor: 'pointer' }}
            >
              Cancel
            </button>
            <button 
              onClick={saveNewTarget}
              disabled={saving}
              style={{ padding: '6px 12px', border: 'none', background: 'var(--success-green)', color: 'white', borderRadius: '4px', cursor: 'pointer' }}
            >
              {saving ? 'Creating...' : 'Create Target'}
            </button>
          </div>
        </div>
      )}

      {addingNew && (
        <div 
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0,0,0,0.5)',
            zIndex: 999
          }}
          onClick={cancelAddingNew}
        />
      )}
    </div>
  );
};

export default Targets;