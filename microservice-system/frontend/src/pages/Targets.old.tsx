import React, { useState, useEffect } from 'react';
import { targetApi, credentialApi } from '../services/api';
import { Target, TargetCreate, Credential } from '../types';
import EnhancedTargetManagement from '../components/EnhancedTargetManagement';

type ViewMode = 'legacy' | 'enhanced';

const Targets: React.FC = () => {
  const [targets, setTargets] = useState<Target[]>([]);
  const [credentials, setCredentials] = useState<Credential[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [testingTarget, setTestingTarget] = useState<number | null>(null);
  const [editingTarget, setEditingTarget] = useState<Target | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('enhanced');
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

  useEffect(() => {
    // Remove auth dependency - just fetch data immediately like working pages
    fetchTargets();
    fetchCredentials();
  }, []);

  const fetchTargets = async () => {
    try {
      const response = await targetApi.list();
      setTargets(response.targets || []);
    } catch (error) {
      console.error('Failed to fetch targets:', error);
      setTargets([]); // Set empty array on error
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
      setCredentials([]); // Set empty array on error
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingTarget) {
        await targetApi.update(editingTarget.id, formData);
      } else {
        await targetApi.create(formData);
      }
      setShowCreateModal(false);
      setEditingTarget(null);
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
      fetchTargets();
    } catch (error) {
      console.error(`Failed to ${editingTarget ? 'update' : 'create'} target:`, error);
    }
  };

  const resetForm = () => {
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
    setEditingTarget(null);
  };

  const handleEdit = (target: Target) => {
    setEditingTarget(target);
    setFormData({
      name: target.name,
      hostname: target.hostname,
      ip_address: target.ip_address || '',
      protocol: target.protocol,
      port: target.port,
      os_type: target.os_type,
      credential_ref: target.credential_ref,
      tags: target.tags,
      metadata: target.metadata,
      depends_on: target.depends_on
    });
    setShowCreateModal(true);
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this target?')) {
      try {
        await targetApi.delete(id);
        fetchTargets();
      } catch (error) {
        console.error('Failed to delete target:', error);
      }
    }
  };

  const handleTestConnection = async (id: number, protocol: string) => {
    setTestingTarget(id);
    try {
      let result;
      if (protocol === 'winrm') {
        result = await targetApi.testWinRM(id);
      } else if (protocol === 'ssh') {
        result = await targetApi.testSSH(id);
      } else {
        throw new Error(`Unsupported protocol: ${protocol}`);
      }

      if (result.test?.status === 'success') {
        alert(`Connection Test Successful!\n\nDetails:\n${JSON.stringify(result.test.details, null, 2)}\n\nNote: ${result.note || 'Test completed'}`);
      } else {
        alert(`Connection Test Failed:\n${result.test?.details?.message || 'Unknown error'}\n\nNote: ${result.note || 'Test completed'}`);
      }
    } catch (error: any) {
      console.error('Test connection error:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Unknown error occurred';
      alert(`Test failed: ${errorMessage}`);
    } finally {
      setTestingTarget(null);
    }
  };

  const getCredentialName = (credId: number) => {
    const cred = (credentials || []).find(c => c.id === credId);
    return cred ? cred.name : `ID: ${credId}`;
  };

  // Show loading while data is being fetched
  if (loading) return <div>Loading targets...</div>;

  // If enhanced view is selected, render the enhanced component
  if (viewMode === 'enhanced') {
    return <EnhancedTargetManagement />;
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h1>Targets</h1>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <div style={{ display: 'flex', gap: '5px' }}>
            <button 
              className={`btn ${(viewMode as string) === 'enhanced' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setViewMode('enhanced')}
              style={{ fontSize: '12px' }}
            >
              Enhanced View
            </button>
            <button 
              className={`btn ${(viewMode as string) === 'legacy' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setViewMode('legacy')}
              style={{ fontSize: '12px' }}
            >
              Legacy View
            </button>
          </div>
          <button 
            className="btn btn-primary"
            onClick={() => {
              resetForm();
              setShowCreateModal(true);
            }}
          >
            Add Target
          </button>
        </div>
      </div>

      <div className="card">
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Hostname</th>
              <th>IP Address</th>
              <th>Protocol</th>
              <th>OS Type</th>
              <th>Port</th>
              <th>Credential</th>
              <th>Tags</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {(targets || []).map(target => (
              <tr key={target.id}>
                <td>{target.id}</td>
                <td>{target.name}</td>
                <td>{target.hostname}</td>
                <td>{target.ip_address || '-'}</td>
                <td>
                  <span className="status" style={{ 
                    backgroundColor: target.protocol === 'winrm' ? '#d4edda' : '#d1ecf1',
                    color: target.protocol === 'winrm' ? '#155724' : '#0c5460'
                  }}>
                    {target.protocol}
                  </span>
                </td>
                <td>
                  <span className="status" style={{ 
                    backgroundColor: 
                      target.os_type === 'windows' ? '#e2e3e5' : 
                      target.os_type === 'linux' ? '#d1ecf1' :
                      target.os_type === 'unix' ? '#fff3cd' :
                      '#f8d7da',
                    color: 
                      target.os_type === 'windows' ? '#383d41' : 
                      target.os_type === 'linux' ? '#0c5460' :
                      target.os_type === 'unix' ? '#856404' :
                      '#721c24'
                  }}>
                    {target.os_type}
                  </span>
                </td>
                <td>{target.port}</td>
                <td>{getCredentialName(target.credential_ref)}</td>
                <td>{target.tags.join(', ') || '-'}</td>
                <td>
                  <div style={{ display: 'flex', gap: '5px' }}>
                    {(target.protocol === 'winrm' || target.protocol === 'ssh') && (
                      <button 
                        className="btn btn-secondary"
                        onClick={() => handleTestConnection(target.id, target.protocol)}
                        disabled={testingTarget === target.id}
                        style={{ fontSize: '12px' }}
                      >
                        {testingTarget === target.id ? 'Testing...' : 'Test'}
                      </button>
                    )}
                    <button 
                      className="btn btn-primary"
                      onClick={() => handleEdit(target)}
                      style={{ fontSize: '12px' }}
                    >
                      Edit
                    </button>
                    <button 
                      className="btn btn-danger"
                      onClick={() => handleDelete(target.id)}
                      style={{ fontSize: '12px' }}
                    >
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Create Target Modal */}
      {showCreateModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div className="card" style={{ width: '500px', margin: '20px' }}>
            <h3>{editingTarget ? 'Edit Target' : 'Add New Target'}</h3>
            <form onSubmit={handleCreate}>
              <div className="form-group">
                <label>Name:</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  required
                />
              </div>
              
              <div className="form-group">
                <label>Hostname:</label>
                <input
                  type="text"
                  value={formData.hostname}
                  onChange={(e) => setFormData({...formData, hostname: e.target.value})}
                  required
                />
              </div>

              <div className="form-group">
                <label>IP Address:</label>
                <input
                  type="text"
                  value={formData.ip_address}
                  onChange={(e) => setFormData({...formData, ip_address: e.target.value})}
                  placeholder="Optional - e.g., 192.168.1.100"
                />
              </div>

              <div className="form-group">
                <label>Protocol:</label>
                <select 
                  value={formData.protocol}
                  onChange={(e) => {
                    const protocol = e.target.value;
                    setFormData({
                      ...formData, 
                      protocol,
                      port: protocol === 'winrm' ? 5985 : protocol === 'ssh' ? 22 : 80,
                      os_type: protocol === 'winrm' ? 'windows' : protocol === 'ssh' ? 'linux' : formData.os_type
                    });
                  }}
                >
                  <option value="winrm">WinRM</option>
                  <option value="ssh">SSH</option>
                  <option value="http">HTTP</option>
                </select>
              </div>

              <div className="form-group">
                <label>OS Type:</label>
                <select 
                  value={formData.os_type}
                  onChange={(e) => setFormData({...formData, os_type: e.target.value})}
                >
                  <option value="windows">Windows</option>
                  <option value="linux">Linux</option>
                  <option value="unix">Unix</option>
                  <option value="network">Network Device</option>
                  <option value="other">Other</option>
                </select>
              </div>

              <div className="form-group">
                <label>Port:</label>
                <input
                  type="number"
                  value={formData.port}
                  onChange={(e) => setFormData({...formData, port: parseInt(e.target.value)})}
                  required
                />
              </div>

              <div className="form-group">
                <label>Credential:</label>
                <select 
                  value={formData.credential_ref}
                  onChange={(e) => setFormData({...formData, credential_ref: parseInt(e.target.value)})}
                  required
                >
                  <option value={0}>Select credential...</option>
                  {(credentials || []).map(cred => (
                    <option key={cred.id} value={cred.id}>
                      {cred.name} ({cred.credential_type})
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Tags (comma-separated):</label>
                <input
                  type="text"
                  value={formData.tags?.join(', ') || ''}
                  onChange={(e) => setFormData({...formData, tags: e.target.value.split(',').map(t => t.trim()).filter(t => t)})}
                />
              </div>

              <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
                <button type="submit" className="btn btn-primary">
                  {editingTarget ? 'Update Target' : 'Create Target'}
                </button>
                <button 
                  type="button" 
                  className="btn btn-secondary"
                  onClick={() => {
                    setShowCreateModal(false);
                    resetForm();
                  }}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Targets;