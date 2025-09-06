import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Plus, Trash2, Check, X, Edit3, MonitorCheck } from 'lucide-react';
import { targetApi, credentialApi } from '../services/api';
import { enhancedTargetApi, targetServiceApi, targetCredentialApi } from '../services/enhancedApi';
import { Target, TargetCreate, Credential } from '../types';
import { EnhancedTarget, TargetService, TargetCredential } from '../types/enhanced';

// Service type definitions with default ports
const SERVICE_TYPES = {
  // Remote Access
  'SSH': 22,
  'RDP': 3389,
  'VNC': 5900,
  'Telnet': 23,
  
  // Windows Management  
  'WinRM HTTP': 5985,
  'WinRM HTTPS': 5986,
  'WMI': 135,
  'SMB': 445,
  
  // Web Services
  'HTTP': 80,
  'HTTPS': 443,
  'HTTP Alt': 8080,
  'HTTPS Alt': 8443,
  
  // Database Services
  'MySQL': 3306,
  'PostgreSQL': 5432,
  'SQL Server': 1433,
  'Oracle': 1521,
  'MongoDB': 27017,
  'Redis': 6379,
  
  // Email Services
  'SMTP': 25,
  'SMTP SSL': 465,
  'SMTP TLS': 587,
  'IMAP': 143,
  'IMAPS': 993,
  'POP3': 110,
  'POP3S': 995,
  
  // File Transfer
  'FTP': 21,
  'FTPS': 990,
  'SFTP': 22,
  
  // Network Services
  'DNS': 53,
  'SNMP': 161,
  'NTP': 123,
} as const;

interface EditingState {
  targetId: number;
  field: 'name' | 'hostname' | 'ip_address' | 'description' | 'tags';
  value: string;
}

interface NewTargetService {
  service_type: string;
  port: number;
  credential_id?: number;
}

interface NewTargetState {
  ip_address: string;
  os_type: string;
  tags: string[];
  description: string;
  services: NewTargetService[];
}

const Targets: React.FC = () => {
  const navigate = useNavigate();
  const { action, id } = useParams<{ action?: string; id?: string }>();
  const [targets, setTargets] = useState<EnhancedTarget[]>([]);
  const [credentials, setCredentials] = useState<Credential[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [editing, setEditing] = useState<EditingState | null>(null);

  const [testingService, setTestingService] = useState<number | null>(null);
  const [selectedTarget, setSelectedTarget] = useState<EnhancedTarget | null>(null);
  const [addingNew, setAddingNew] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const [newTarget, setNewTarget] = useState<NewTargetState>({
    ip_address: '',
    os_type: '',
    tags: [],
    description: '',
    services: []
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
    setEditing(null);
  };

  const startEditing = (targetId: number, field: 'name' | 'hostname' | 'ip_address' | 'description' | 'tags', currentValue: string = '') => {
    setEditing({
      targetId,
      field,
      value: currentValue
    });
    setAddingNew(false);
  };

  const cancelEditing = () => {
    setEditing(null);
  };

  const saveEdit = async () => {
    if (!editing) return;

    if ((editing.field === 'name' || editing.field === 'hostname') && !editing.value.trim()) {
      alert(`${editing.field} cannot be empty`);
      return;
    }



    try {
      setSaving(true);
      const target = targets.find(t => t.id === editing.targetId);
      if (!target) return;

      let updateData: any = {};
      
      if (editing.field === 'tags') {
        updateData.tags = editing.value ? editing.value.split(',').map(tag => tag.trim()).filter(tag => tag) : [];
      } else {
        updateData[editing.field] = editing.value;
      }
      
      await enhancedTargetApi.update(editing.targetId, updateData);
      await fetchTargets();
      
      if (selectedTarget?.id === editing.targetId) {
        if (editing.field === 'tags') {
          setSelectedTarget({...selectedTarget, tags: updateData.tags});
        } else {
          setSelectedTarget({...selectedTarget, [editing.field]: editing.value});
        }
      }
      
      setEditing(null);
    } catch (error) {
      console.error(`Failed to update ${editing.field}:`, error);
      alert(`Failed to update ${editing.field}`);
    } finally {
      setSaving(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      saveEdit();
    } else if (e.key === 'Escape') {
      cancelEditing();
    }
  };

  const cancelAddingNew = () => {
    setAddingNew(false);
    setNewTarget({
      ip_address: '',
      os_type: '',
      tags: [],
      description: '',
      services: []
    });
  };

  // Service management functions
  const addService = () => {
    setNewTarget({
      ...newTarget,
      services: [...newTarget.services, { service_type: '', port: 22, credential_id: undefined }]
    });
  };

  const removeService = (index: number) => {
    setNewTarget({
      ...newTarget,
      services: newTarget.services.filter((_, i) => i !== index)
    });
  };

  const updateService = (index: number, field: keyof NewTargetService, value: any) => {
    const updatedServices = [...newTarget.services];
    if (field === 'service_type') {
      // Auto-populate port when service type changes
      const defaultPort = SERVICE_TYPES[value as keyof typeof SERVICE_TYPES];
      updatedServices[index] = {
        ...updatedServices[index],
        service_type: value,
        port: defaultPort || 22
      };
    } else {
      updatedServices[index] = {
        ...updatedServices[index],
        [field]: value
      };
    }
    setNewTarget({
      ...newTarget,
      services: updatedServices
    });
  };

  const saveNewTarget = async () => {
    if (!newTarget.ip_address.trim()) {
      alert('IP Address or FQDN is required');
      return;
    }

    try {
      setSaving(true);
      const targetToCreate: TargetCreate = {
        name: newTarget.ip_address, // Use IP/FQDN as the name for now
        hostname: newTarget.ip_address, // Use IP/FQDN as hostname for now
        ip_address: newTarget.ip_address,
        protocol: 'ssh', // Default protocol - will be replaced by service-level configs
        port: 22, // Default port - will be replaced by service-level configs  
        os_type: newTarget.os_type || 'unknown',
        credential_ref: 1, // Default credential - will be replaced by service-level configs
        tags: newTarget.tags,
        metadata: { description: newTarget.description },
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
                    <th>IP Address/FQDN</th>
                    <th>OS</th>
                    <th>Status</th>
                    <th>Tags</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>


                  {/* Existing Targets */}
                  {targets.map((target) => (
                    <tr 
                      key={target.id} 
                      className={selectedTarget?.id === target.id ? 'selected' : ''}
                      onClick={() => handleTargetClick(target)}
                    >
                      <td style={{ fontWeight: '500' }}>{target.ip_address || '-'}</td>
                      <td>{target.os_type}</td>
                      <td>
                        <span className={`status-badge ${getStatusBadge(getTargetStatus(target))}`}>
                          {getTargetStatus(target)}
                        </span>
                      </td>
                      <td>{target.tags?.length ? target.tags.join(', ') : '-'}</td>
                      <td>
                        <div style={{ display: 'flex', gap: '4px' }}>
                          <button 
                            className="btn-icon btn-secondary"
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedTarget(target);
                            }}
                            title="Edit target details"
                          >
                            <Edit3 size={16} />
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
                        </div>
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
          <div className="section-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>{addingNew ? 'Create New Target' : selectedTarget ? `Target Details` : 'Select Target'}</span>
            {addingNew && (
              <div style={{ display: 'flex', gap: '8px' }}>
                <button 
                  onClick={saveNewTarget}
                  className="btn-icon btn-success"
                  disabled={saving}
                  title="Create Target"
                >
                  <Check size={16} />
                </button>
                <button 
                  onClick={cancelAddingNew}
                  className="btn-icon btn-ghost"
                  title="Cancel"
                >
                  <X size={16} />
                </button>
              </div>
            )}
          </div>
          <div className="compact-content">
            {addingNew ? (
              <div className="target-details">
                <style>{`
                  .subtle-input {
                    width: 100%;
                    padding: 8px 12px;
                    border: 1px solid var(--neutral-200);
                    background: white;
                    border-radius: 4px;
                    font-size: 13px;
                    color: var(--neutral-900);
                  }
                  .subtle-input:focus {
                    outline: none;
                  }
                  .subtle-input::placeholder {
                    color: var(--neutral-400);
                  }
                  .subtle-select {
                    width: 100%;
                    padding: 8px 12px;
                    border: 1px solid var(--neutral-200);
                    background: white;
                    border-radius: 4px;
                    font-size: 13px;
                    color: var(--neutral-900);
                    cursor: pointer;
                  }
                  .subtle-select:focus {
                    outline: none;
                  }
                  .target-form-grid {
                    display: grid;
                    grid-template-columns: 2fr 1fr 1fr;
                    gap: 20px;
                    margin-bottom: 20px;
                  }
                  .form-field {
                    display: flex;
                    flex-direction: column;
                    gap: 2px;
                  }
                  .form-label {
                    font-size: 12px;
                    font-weight: 600;
                    color: var(--neutral-700);
                  }
                  .form-label.required::after {
                    content: ' *';
                    color: var(--primary-red);
                  }
                  .char-counter {
                    font-size: 11px;
                    color: var(--neutral-500);
                    text-align: right;
                    margin-top: 2px;
                  }
                `}</style>
                <div className="target-form-grid">
                  {/* Column 1 - Primary Field */}
                  <div>
                    <div className="form-field">
                      <label className="form-label required">IP Address / FQDN</label>
                      <input
                        type="text"
                        value={newTarget.ip_address}
                        onChange={(e) => setNewTarget({...newTarget, ip_address: e.target.value})}
                        className="subtle-input"
                        autoFocus
                      />
                    </div>

                    <div className="form-field">
                      <label className="form-label">Tags</label>
                      <input
                        type="text"
                        value={newTarget.tags.join(', ')}
                        onChange={(e) => setNewTarget({...newTarget, tags: e.target.value.split(',').map(t => t.trim()).filter(t => t)})}
                        className="subtle-input"
                      />
                    </div>
                  </div>

                  {/* Column 2 */}
                  <div>
                    <div className="form-field">
                      <label className="form-label">Operating System</label>
                      <select 
                        value={newTarget.os_type} 
                        onChange={(e) => setNewTarget({...newTarget, os_type: e.target.value})}
                        className="subtle-select"
                      >
                        <option value="">Select OS</option>
                        <option value="windows">Windows</option>
                        <option value="linux">Linux</option>
                        <option value="macos">macOS</option>
                      </select>
                    </div>
                  </div>

                  {/* Column 3 */}
                  <div>
                    <div className="form-field">
                      <label className="form-label">Description</label>
                      <input
                        type="text"
                        value={newTarget.description}
                        onChange={(e) => {
                          const value = e.target.value;
                          if (value.length <= 20) {
                            setNewTarget({...newTarget, description: value});
                          }
                        }}
                        className="subtle-input"
                        maxLength={20}
                      />
                    </div>
                  </div>
                </div>

                {/* Services Section */}
                <div style={{ marginTop: '20px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                    <label className="form-label" style={{ margin: 0 }}>Services & Communication Types</label>
                    <button 
                      onClick={addService}
                      className="btn-icon btn-success"
                      title="Add Service"
                      type="button"
                    >
                      <Plus size={14} />
                    </button>
                  </div>

                  {newTarget.services.length === 0 ? (
                    <div style={{ 
                      padding: '12px 0', 
                      color: 'var(--neutral-500)',
                      fontSize: '13px',
                      textAlign: 'center',
                      fontStyle: 'italic'
                    }}>
                      No services configured. Click + to add a service.
                    </div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      {newTarget.services.map((service, index) => (
                        <div key={index} style={{ 
                          display: 'grid', 
                          gridTemplateColumns: '2fr 1fr 2fr auto auto', 
                          gap: '12px', 
                          alignItems: 'center',
                          padding: '0',
                          marginBottom: '12px'
                        }}>
                          {/* Service Type */}
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                            <label style={{ fontSize: '11px', color: 'var(--neutral-600)', fontWeight: '500', margin: 0 }}>Service Type</label>
                            <select
                              value={service.service_type}
                              onChange={(e) => updateService(index, 'service_type', e.target.value)}
                              className="subtle-select"
                              style={{ fontSize: '12px' }}
                            >
                              <option value="">Select Service</option>
                              <optgroup label="Remote Access">
                                <option value="SSH">SSH</option>
                                <option value="RDP">RDP</option>
                                <option value="VNC">VNC</option>
                                <option value="Telnet">Telnet</option>
                              </optgroup>
                              <optgroup label="Windows Management">
                                <option value="WinRM HTTP">WinRM HTTP</option>
                                <option value="WinRM HTTPS">WinRM HTTPS</option>
                                <option value="WMI">WMI</option>
                                <option value="SMB">SMB</option>
                              </optgroup>
                              <optgroup label="Web Services">
                                <option value="HTTP">HTTP</option>
                                <option value="HTTPS">HTTPS</option>
                                <option value="HTTP Alt">HTTP Alt</option>
                                <option value="HTTPS Alt">HTTPS Alt</option>
                              </optgroup>
                              <optgroup label="Database Services">
                                <option value="MySQL">MySQL</option>
                                <option value="PostgreSQL">PostgreSQL</option>
                                <option value="SQL Server">SQL Server</option>
                                <option value="Oracle">Oracle</option>
                                <option value="MongoDB">MongoDB</option>
                                <option value="Redis">Redis</option>
                              </optgroup>
                              <optgroup label="Email Services">
                                <option value="SMTP">SMTP</option>
                                <option value="SMTP SSL">SMTP SSL</option>
                                <option value="SMTP TLS">SMTP TLS</option>
                                <option value="IMAP">IMAP</option>
                                <option value="IMAPS">IMAPS</option>
                                <option value="POP3">POP3</option>
                                <option value="POP3S">POP3S</option>
                              </optgroup>
                              <optgroup label="File Transfer">
                                <option value="FTP">FTP</option>
                                <option value="FTPS">FTPS</option>
                                <option value="SFTP">SFTP</option>
                              </optgroup>
                              <optgroup label="Network Services">
                                <option value="DNS">DNS</option>
                                <option value="SNMP">SNMP</option>
                                <option value="NTP">NTP</option>
                              </optgroup>
                            </select>
                          </div>

                          {/* Port */}
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                            <label style={{ fontSize: '11px', color: 'var(--neutral-600)', fontWeight: '500', margin: 0 }}>Port</label>
                            <input
                              type="number"
                              value={service.port}
                              onChange={(e) => updateService(index, 'port', parseInt(e.target.value) || 22)}
                              className="subtle-input"
                              style={{ fontSize: '12px' }}
                              min="1"
                              max="65535"
                            />
                          </div>

                          {/* Credential */}
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                            <label style={{ fontSize: '11px', color: 'var(--neutral-600)', fontWeight: '500', margin: 0 }}>Credential</label>
                            <select
                              value={service.credential_id || ''}
                              onChange={(e) => updateService(index, 'credential_id', e.target.value ? parseInt(e.target.value) : undefined)}
                              className="subtle-select"
                              style={{ fontSize: '12px' }}
                            >
                              <option value="">No Credential</option>
                              {credentials.map(cred => (
                                <option key={cred.id} value={cred.id}>
                                  {cred.name}
                                </option>
                              ))}
                            </select>
                          </div>

                          {/* Test Connection Button */}
                          <div style={{ paddingTop: '14px' }}>
                            <button 
                              className="btn-icon btn-ghost"
                              title="Test Connection"
                              type="button"
                            >
                              <MonitorCheck size={14} />
                            </button>
                          </div>

                          {/* Remove Button */}
                          <div style={{ paddingTop: '14px' }}>
                            <button 
                              onClick={() => removeService(index)}
                              className="btn-icon btn-ghost"
                              title="Remove Service"
                              type="button"
                            >
                              <Trash2 size={14} />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ) : selectedTarget ? (
              <div className="target-details">
                <h3>{selectedTarget.name}</h3>
                
                <div className="detail-group">
                  <div className="detail-label">Name</div>
                  <div className="detail-value">
                    {editing?.targetId === selectedTarget.id && editing?.field === 'name' ? (
                      <div>
                        <input
                          type="text"
                          value={editing.value}
                          onChange={(e) => setEditing({...editing, value: e.target.value})}
                          onKeyDown={handleKeyPress}
                          className="detail-input"
                          autoFocus
                        />
                        <div className="action-buttons">
                          <button onClick={saveEdit} className="btn-icon btn-success" title="Save" disabled={saving}>
                            <Check size={16} />
                          </button>
                          <button onClick={cancelEditing} className="btn-icon btn-ghost" title="Cancel">
                            <X size={16} />
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <span>{selectedTarget.name}</span>
                        <button 
                          className="btn-icon btn-ghost btn-sm"
                          onClick={() => startEditing(selectedTarget.id, 'name', selectedTarget.name)}
                          title="Edit name"
                        >
                          <Edit3 size={14} />
                        </button>
                      </div>
                    )}
                  </div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">Hostname</div>
                  <div className="detail-value">
                    {editing?.targetId === selectedTarget.id && editing?.field === 'hostname' ? (
                      <div>
                        <input
                          type="text"
                          value={editing.value}
                          onChange={(e) => setEditing({...editing, value: e.target.value})}
                          onKeyDown={handleKeyPress}
                          className="detail-input"
                          autoFocus
                        />
                        <div className="action-buttons">
                          <button onClick={saveEdit} className="btn-icon btn-success" title="Save" disabled={saving}>
                            <Check size={16} />
                          </button>
                          <button onClick={cancelEditing} className="btn-icon btn-ghost" title="Cancel">
                            <X size={16} />
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <span>{selectedTarget.hostname}</span>
                        <button 
                          className="btn-icon btn-ghost btn-sm"
                          onClick={() => startEditing(selectedTarget.id, 'hostname', selectedTarget.hostname)}
                          title="Edit hostname"
                        >
                          <Edit3 size={14} />
                        </button>
                      </div>
                    )}
                  </div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">IP Address</div>
                  <div className="detail-value">
                    {editing?.targetId === selectedTarget.id && editing?.field === 'ip_address' ? (
                      <div>
                        <input
                          type="text"
                          value={editing.value}
                          onChange={(e) => setEditing({...editing, value: e.target.value})}
                          onKeyDown={handleKeyPress}
                          className="detail-input"
                          autoFocus
                        />
                        <div className="action-buttons">
                          <button onClick={saveEdit} className="btn-icon btn-success" title="Save" disabled={saving}>
                            <Check size={16} />
                          </button>
                          <button onClick={cancelEditing} className="btn-icon btn-ghost" title="Cancel">
                            <X size={16} />
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <span>{selectedTarget.ip_address || '-'}</span>
                        <button 
                          className="btn-icon btn-ghost btn-sm"
                          onClick={() => startEditing(selectedTarget.id, 'ip_address', selectedTarget.ip_address || '')}
                          title="Edit IP address"
                        >
                          <Edit3 size={14} />
                        </button>
                      </div>
                    )}
                  </div>
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
                  <div className="detail-value">
                    {editing?.targetId === selectedTarget.id && editing?.field === 'description' ? (
                      <div>
                        <textarea
                          value={editing.value}
                          onChange={(e) => setEditing({...editing, value: e.target.value})}
                          onKeyDown={handleKeyPress}
                          className="detail-textarea"
                          autoFocus
                        />
                        <div className="action-buttons">
                          <button onClick={saveEdit} className="btn-icon btn-success" title="Save" disabled={saving}>
                            <Check size={16} />
                          </button>
                          <button onClick={cancelEditing} className="btn-icon btn-ghost" title="Cancel">
                            <X size={16} />
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <span>{selectedTarget.description || '-'}</span>
                        <button 
                          className="btn-icon btn-ghost btn-sm"
                          onClick={() => startEditing(selectedTarget.id, 'description', selectedTarget.description || '')}
                          title="Edit description"
                        >
                          <Edit3 size={14} />
                        </button>
                      </div>
                    )}
                  </div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">Tags</div>
                  <div className="detail-value">
                    {editing?.targetId === selectedTarget.id && editing?.field === 'tags' ? (
                      <div>
                        <input
                          type="text"
                          value={editing.value}
                          onChange={(e) => setEditing({...editing, value: e.target.value})}
                          onKeyDown={handleKeyPress}
                          className="detail-input"
                          placeholder="Comma-separated tags (e.g. web,production,database)"
                          autoFocus
                        />
                        <div className="action-buttons">
                          <button onClick={saveEdit} className="btn-icon btn-success" title="Save" disabled={saving}>
                            <Check size={16} />
                          </button>
                          <button onClick={cancelEditing} className="btn-icon btn-ghost" title="Cancel">
                            <X size={16} />
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <span>
                          {selectedTarget.tags?.length ? (
                            <div className="tag-list">
                              {selectedTarget.tags.map((tag, index) => (
                                <span key={index} className="tag">{tag}</span>
                              ))}
                            </div>
                          ) : '-'}
                        </span>
                        <button 
                          className="btn-icon btn-ghost btn-sm"
                          onClick={() => startEditing(selectedTarget.id, 'tags', selectedTarget.tags?.join(', ') || '')}
                          title="Edit tags"
                        >
                          <Edit3 size={14} />
                        </button>
                      </div>
                    )}
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
                              <MonitorCheck size={14} />
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




    </div>
  );
};

export default Targets;