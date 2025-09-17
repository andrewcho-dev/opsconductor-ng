import React, { useState, useEffect } from 'react';
import { 
  Plus, 
  Search, 
  Filter, 
  Edit, 
  Trash2, 
  Check, 
  X, 
  MonitorCheck,
  ChevronDown,
  ChevronRight,
  AlertTriangle,
  CheckCircle,
  Clock,
  Zap
} from 'lucide-react';

// Service type mappings
const SERVICE_TYPES = {
  ssh: 22,
  rdp: 3389,
  http: 80,
  https: 443,
  ftp: 21,
  telnet: 23,
  smtp: 25,
  dns: 53,
  snmp: 161,
  mysql: 3306,
  postgresql: 5432,
  mongodb: 27017,
  redis: 6379,
  elasticsearch: 9200,
  custom: null
};

const SERVICE_DISPLAY_NAMES = {
  ssh: 'SSH',
  rdp: 'RDP',
  http: 'HTTP',
  https: 'HTTPS',
  ftp: 'FTP',
  telnet: 'Telnet',
  smtp: 'SMTP',
  dns: 'DNS',
  snmp: 'SNMP',
  mysql: 'MySQL',
  postgresql: 'PostgreSQL',
  mongodb: 'MongoDB',
  redis: 'Redis',
  elasticsearch: 'Elasticsearch',
  custom: 'Custom'
};

const Targets = () => {
  // State management
  const [targets, setTargets] = useState([]);
  const [filteredTargets, setFilteredTargets] = useState([]);
  const [selectedTarget, setSelectedTarget] = useState(null);
  const [editingTarget, setEditingTarget] = useState(null);
  const [addingNew, setAddingNew] = useState(false);
  const [newTarget, setNewTarget] = useState({
    ip_address: '',
    description: '',
    os_type: '',
    tags: [],
    services: []
  });
  const [searchTerm, setSearchTerm] = useState('');
  const [filterTag, setFilterTag] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Unified Target Form Component
  const TargetForm = ({ target, mode, onUpdate, onSave, onCancel }) => {
    const isEditable = mode === 'create' || mode === 'edit';
    const title = mode === 'create' ? 'Create New Target' : 
                  mode === 'edit' ? `Edit Target: ${target.ip_address}` : 
                  `Target Details: ${target.ip_address}`;

    const addService = () => {
      const newService = {
        service_type: '',
        port: '',
        credential_id: ''
      };
      onUpdate({
        ...target,
        services: [...(target.services || []), newService]
      });
    };

    const updateService = (index, field, value) => {
      const updatedServices = [...(target.services || [])];
      updatedServices[index] = { ...updatedServices[index], [field]: value };
      
      // Auto-fill port when service type is selected
      if (field === 'service_type' && SERVICE_TYPES[value]) {
        updatedServices[index].port = SERVICE_TYPES[value];
      }
      
      onUpdate({ ...target, services: updatedServices });
    };

    const removeService = (index) => {
      const updatedServices = target.services.filter((_, i) => i !== index);
      onUpdate({ ...target, services: updatedServices });
    };

    return (
      <>
        <div className="section-header">
          <span>{title}</span>
          <div style={{ display: 'flex', gap: '4px' }}>
            {mode === 'create' && (
              <>
                <button 
                  className="btn-icon btn-success"
                  onClick={onSave}
                  disabled={saving}
                  title="Create Target"
                >
                  <Check size={16} />
                </button>
                <button 
                  className="btn-icon btn-ghost"
                  onClick={onCancel}
                  disabled={saving}
                  title="Cancel"
                >
                  <X size={16} />
                </button>
              </>
            )}
            {mode === 'edit' && (
              <>
                <button 
                  className="btn-icon btn-success"
                  onClick={onSave}
                  disabled={saving}
                  title="Update Target"
                >
                  <Check size={16} />
                </button>
                <button 
                  className="btn-icon btn-ghost"
                  onClick={onCancel}
                  disabled={saving}
                  title="Cancel"
                >
                  <X size={16} />
                </button>
              </>
            )}
            {mode === 'view' && (
              <button 
                className="btn-icon btn-primary"
                onClick={() => setEditingTarget({...target})}
                title="Edit Target"
              >
                <Edit size={16} />
              </button>
            )}
          </div>
        </div>
        
        <div className="compact-content">
          <div className="target-form">
            <style>{`
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
              .form-input {
                width: 100%;
                padding: 8px 12px;
                border: 1px solid var(--neutral-300);
                background: white;
                border-radius: 4px;
                font-size: 13px;
                color: var(--neutral-900);
              }
              .form-input:focus {
                outline: none;
                border-color: var(--primary-blue);
                box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
              }
              .form-input:disabled {
                background: var(--neutral-50);
                color: var(--neutral-600);
                cursor: not-allowed;
              }
              .form-input::placeholder {
                color: var(--neutral-400);
              }
              .form-select {
                width: 100%;
                padding: 8px 12px;
                border: 1px solid var(--neutral-300);
                background: white;
                border-radius: 4px;
                font-size: 13px;
                color: var(--neutral-900);
                cursor: pointer;
              }
              .form-select:focus {
                outline: none;
                border-color: var(--primary-blue);
                box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
              }
              .form-select:disabled {
                background: var(--neutral-50);
                color: var(--neutral-600);
                cursor: not-allowed;
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
                    value={target.ip_address || ''}
                    onChange={(e) => isEditable && onUpdate({...target, ip_address: e.target.value})}
                    className="form-input"
                    disabled={!isEditable}
                    autoFocus={mode === 'create'}
                  />
                </div>

                <div className="form-field">
                  <label className="form-label">Tags</label>
                  <input
                    type="text"
                    value={target.tags?.join(', ') || ''}
                    onChange={(e) => isEditable && onUpdate({...target, tags: e.target.value.split(',').map(t => t.trim()).filter(t => t)})}
                    className="form-input"
                    disabled={!isEditable}
                    placeholder="Comma-separated tags (e.g. web,production,database)"
                  />
                </div>
              </div>

              {/* Column 2 */}
              <div>
                <div className="form-field">
                  <label className="form-label">Operating System</label>
                  <select 
                    value={target.os_type || ''} 
                    onChange={(e) => isEditable && onUpdate({...target, os_type: e.target.value})}
                    className="form-select"
                    disabled={!isEditable}
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
                    value={target.description || ''}
                    onChange={(e) => {
                      if (isEditable) {
                        const value = e.target.value;
                        if (value.length <= 20) {
                          onUpdate({...target, description: value});
                        }
                      }
                    }}
                    className="form-input"
                    disabled={!isEditable}
                    maxLength={20}
                  />
                  <div className="char-counter">
                    {(target.description || '').length}/20
                  </div>
                </div>
              </div>
            </div>

            {/* Services Section */}
            <div style={{ marginTop: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <label className="form-label" style={{ margin: 0 }}>Services & Communication Types</label>
                <span style={{ 
                  fontSize: '12px', 
                  color: 'var(--neutral-500)',
                  fontWeight: 'normal'
                }}>
                  ({target.services?.length || 0} configured)
                </span>
                {isEditable && (
                  <button 
                    onClick={addService}
                    className="btn-icon btn-primary"
                    title="Add Service"
                    type="button"
                    style={{ marginLeft: 'auto' }}
                  >
                    <Plus size={14} />
                  </button>
                )}
              </div>

              {!target.services || target.services.length === 0 ? (
                <div style={{ 
                  padding: '12px 0', 
                  color: 'var(--neutral-500)',
                  fontSize: '13px',
                  textAlign: 'center',
                  fontStyle: 'italic'
                }}>
                  No services configured. {isEditable && 'Click + to add a service.'}
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {target.services.map((service, index) => (
                    <div key={index} style={{ 
                      display: 'grid', 
                      gridTemplateColumns: isEditable ? '2fr 1fr 2fr auto auto' : '2fr 1fr 2fr auto', 
                      gap: '12px', 
                      alignItems: 'end',
                      padding: '8px',
                      backgroundColor: 'var(--neutral-50)',
                      borderRadius: '4px',
                      border: '1px solid var(--neutral-200)'
                    }}>
                      {/* Service Type */}
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                        <label style={{ fontSize: '11px', color: 'var(--neutral-600)', fontWeight: '500', margin: 0 }}>Service Type</label>
                        <select
                          value={service.service_type || ''}
                          onChange={(e) => isEditable && updateService(index, 'service_type', e.target.value)}
                          className="form-select"
                          style={{ fontSize: '12px', padding: '6px 8px' }}
                          disabled={!isEditable}
                        >
                          <option value="">Select Service</option>
                          {Object.entries(SERVICE_TYPES).map(([type, port]) => (
                            <option key={type} value={type}>
                              {SERVICE_DISPLAY_NAMES[type] || type} ({port})
                            </option>
                          ))}
                        </select>
                      </div>

                      {/* Port */}
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                        <label style={{ fontSize: '11px', color: 'var(--neutral-600)', fontWeight: '500', margin: 0 }}>Port</label>
                        <input
                          type="number"
                          value={service.port || ''}
                          onChange={(e) => isEditable && updateService(index, 'port', parseInt(e.target.value) || '')}
                          className="form-input"
                          style={{ fontSize: '12px', padding: '6px 8px' }}
                          placeholder="Port"
                          disabled={!isEditable}
                        />
                      </div>

                      {/* Credential */}
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                        <label style={{ fontSize: '11px', color: 'var(--neutral-600)', fontWeight: '500', margin: 0 }}>Credential</label>
                        <input
                          type="text"
                          value={service.credential_id || ''}
                          onChange={(e) => isEditable && updateService(index, 'credential_id', e.target.value)}
                          className="form-input"
                          style={{ fontSize: '12px', padding: '6px 8px' }}
                          placeholder="Credential ID"
                          disabled={!isEditable}
                        />
                      </div>

                      {/* Test Button */}
                      <div style={{ paddingTop: '14px' }}>
                        <button 
                          className="btn-icon btn-ghost"
                          title="Test Connection"
                          type="button"
                        >
                          <MonitorCheck size={14} />
                        </button>
                      </div>

                      {/* Remove Button - only show in edit mode */}
                      {isEditable && (
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
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </>
    );
  };

  // Event handlers
  const saveNewTarget = async () => {
    setSaving(true);
    try {
      // API call would go here
      console.log('Saving new target:', newTarget);
      setTargets([...targets, { ...newTarget, id: Date.now() }]);
      setAddingNew(false);
      setNewTarget({
        ip_address: '',
        description: '',
        os_type: '',
        tags: [],
        services: []
      });
    } catch (error) {
      console.error('Error saving target:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleSaveEdit = async () => {
    setSaving(true);
    try {
      // API call would go here
      console.log('Saving edited target:', editingTarget);
      setTargets(targets.map(t => t.id === editingTarget.id ? editingTarget : t));
      setSelectedTarget(editingTarget);
      setEditingTarget(null);
    } catch (error) {
      console.error('Error updating target:', error);
    } finally {
      setSaving(false);
    }
  };

  const cancelAddingNew = () => {
    setAddingNew(false);
    setNewTarget({
      ip_address: '',
      description: '',
      os_type: '',
      tags: [],
      services: []
    });
  };

  const handleCancelEdit = () => {
    setEditingTarget(null);
  };

  // Load targets on component mount
  useEffect(() => {
    const loadTargets = async () => {
      setLoading(true);
      try {
        // Mock data for now
        const mockTargets = [
          {
            id: 1,
            ip_address: '192.168.1.100',
            description: 'Web Server',
            os_type: 'linux',
            tags: ['web', 'production'],
            services: [
              { service_type: 'ssh', port: 22, credential_id: 'admin-ssh' },
              { service_type: 'http', port: 80, credential_id: '' }
            ]
          },
          {
            id: 2,
            ip_address: '10.0.0.50',
            description: 'Database',
            os_type: 'windows',
            tags: ['database', 'critical'],
            services: [
              { service_type: 'rdp', port: 3389, credential_id: 'admin-rdp' },
              { service_type: 'mysql', port: 3306, credential_id: 'db-admin' }
            ]
          }
        ];
        setTargets(mockTargets);
        setFilteredTargets(mockTargets);
      } catch (error) {
        console.error('Error loading targets:', error);
      } finally {
        setLoading(false);
      }
    };

    loadTargets();
  }, []);

  // Filter targets based on search and filter criteria
  useEffect(() => {
    let filtered = targets;

    if (searchTerm) {
      filtered = filtered.filter(target =>
        target.ip_address.toLowerCase().includes(searchTerm.toLowerCase()) ||
        target.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
        target.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    }

    if (filterTag) {
      filtered = filtered.filter(target =>
        target.tags.includes(filterTag)
      );
    }

    setFilteredTargets(filtered);
  }, [targets, searchTerm, filterTag]);

  // Get all unique tags for filter dropdown
  const allTags = [...new Set(targets.flatMap(target => target.tags))];

  return (
    <div className="targets-page">
      <div className="page-header">
        <h1>Targets</h1>
        <button 
          className="btn-primary"
          onClick={() => setAddingNew(true)}
          disabled={addingNew || editingTarget}
        >
          <Plus size={16} />
          Add Target
        </button>
      </div>

      <div className="dashboard-grid">
        {/* Column 1: Search & Filters */}
        <div className="dashboard-section">
          <div className="section-header">
            <span>Search & Filter</span>
          </div>
          <div className="compact-content">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ position: 'relative' }}>
                <Search size={16} style={{ 
                  position: 'absolute', 
                  left: '12px', 
                  top: '50%', 
                  transform: 'translateY(-50%)', 
                  color: 'var(--neutral-400)' 
                }} />
                <input
                  type="text"
                  placeholder="Search targets..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px 12px 8px 40px',
                    border: '1px solid var(--neutral-300)',
                    borderRadius: '4px',
                    fontSize: '13px'
                  }}
                />
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Filter size={16} style={{ color: 'var(--neutral-400)' }} />
                <select
                  value={filterTag}
                  onChange={(e) => setFilterTag(e.target.value)}
                  style={{
                    flex: 1,
                    padding: '8px 12px',
                    border: '1px solid var(--neutral-300)',
                    borderRadius: '4px',
                    fontSize: '13px'
                  }}
                >
                  <option value="">All Tags</option>
                  {allTags.map(tag => (
                    <option key={tag} value={tag}>{tag}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Column 2: Target List */}
        <div className="dashboard-section">
          <div className="section-header">
            <span>Targets ({filteredTargets.length})</span>
          </div>
          <div className="compact-content">
            {loading ? (
              <div style={{ textAlign: 'center', padding: '20px', color: 'var(--neutral-500)' }}>
                Loading targets...
              </div>
            ) : filteredTargets.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '20px', color: 'var(--neutral-500)' }}>
                No targets found
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {filteredTargets.map(target => (
                  <div
                    key={target.id}
                    onClick={() => !addingNew && !editingTarget && setSelectedTarget(target)}
                    style={{
                      padding: '12px',
                      border: '1px solid var(--neutral-200)',
                      borderRadius: '4px',
                      cursor: addingNew || editingTarget ? 'not-allowed' : 'pointer',
                      backgroundColor: selectedTarget?.id === target.id ? 'var(--primary-50)' : 'white',
                      borderColor: selectedTarget?.id === target.id ? 'var(--primary-200)' : 'var(--neutral-200)',
                      opacity: addingNew || editingTarget ? 0.5 : 1
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '4px' }}>
                      <span style={{ fontWeight: '600', fontSize: '14px' }}>{target.ip_address}</span>
                      <span style={{ 
                        fontSize: '11px', 
                        color: 'var(--neutral-500)',
                        textTransform: 'uppercase'
                      }}>
                        {target.os_type || 'Unknown'}
                      </span>
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--neutral-600)', marginBottom: '6px' }}>
                      {target.description || 'No description'}
                    </div>
                    <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                      {target.tags.map(tag => (
                        <span
                          key={tag}
                          style={{
                            fontSize: '10px',
                            padding: '2px 6px',
                            backgroundColor: 'var(--neutral-100)',
                            color: 'var(--neutral-700)',
                            borderRadius: '3px'
                          }}
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Column 3: Target Details/Form */}
        <div className="dashboard-section">
          {addingNew && (
            <TargetForm
              target={newTarget}
              mode="create"
              onUpdate={setNewTarget}
              onSave={saveNewTarget}
              onCancel={cancelAddingNew}
            />
          )}
          
          {editingTarget && (
            <TargetForm
              target={editingTarget}
              mode="edit"
              onUpdate={setEditingTarget}
              onSave={handleSaveEdit}
              onCancel={handleCancelEdit}
            />
          )}
          
          {selectedTarget && !editingTarget && !addingNew && (
            <TargetForm
              target={selectedTarget}
              mode="view"
              onUpdate={() => {}}
              onSave={() => {}}
              onCancel={() => {}}
            />
          )}
          
          {!addingNew && !editingTarget && !selectedTarget && (
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center', 
              height: '200px',
              color: 'var(--neutral-500)',
              fontSize: '14px'
            }}>
              Select a target to view details
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Targets;