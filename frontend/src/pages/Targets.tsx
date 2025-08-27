import React, { useState, useEffect } from 'react';
import { targetApi, credentialApi } from '../services/api';
import { Target, TargetCreate, Credential } from '../types';

const Targets: React.FC = () => {
  const [targets, setTargets] = useState<Target[]>([]);
  const [credentials, setCredentials] = useState<Credential[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [testingTarget, setTestingTarget] = useState<number | null>(null);
  const [formData, setFormData] = useState<TargetCreate>({
    name: '',
    hostname: '',
    protocol: 'winrm',
    port: 5985,
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
      await targetApi.create(formData);
      setShowCreateModal(false);
      setFormData({
        name: '',
        hostname: '',
        protocol: 'winrm',
        port: 5985,
        credential_ref: 0,
        tags: [],
        metadata: {},
        depends_on: []
      });
      fetchTargets();
    } catch (error) {
      console.error('Failed to create target:', error);
    }
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

  const handleTestConnection = async (id: number) => {
    setTestingTarget(id);
    try {
      const result = await targetApi.testWinRM(id);
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

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h1>Targets</h1>
        <button 
          className="btn btn-primary"
          onClick={() => setShowCreateModal(true)}
        >
          Add Target
        </button>
      </div>

      <div className="card">
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Hostname</th>
              <th>Protocol</th>
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
                <td>
                  <span className="status" style={{ 
                    backgroundColor: target.protocol === 'winrm' ? '#d4edda' : '#d1ecf1',
                    color: target.protocol === 'winrm' ? '#155724' : '#0c5460'
                  }}>
                    {target.protocol}
                  </span>
                </td>
                <td>{target.port}</td>
                <td>{getCredentialName(target.credential_ref)}</td>
                <td>{target.tags.join(', ') || '-'}</td>
                <td>
                  <div style={{ display: 'flex', gap: '5px' }}>
                    {target.protocol === 'winrm' && (
                      <button 
                        className="btn btn-secondary"
                        onClick={() => handleTestConnection(target.id)}
                        disabled={testingTarget === target.id}
                        style={{ fontSize: '12px' }}
                      >
                        {testingTarget === target.id ? 'Testing...' : 'Test'}
                      </button>
                    )}
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
            <h3>Add New Target</h3>
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
                <label>Protocol:</label>
                <select 
                  value={formData.protocol}
                  onChange={(e) => setFormData({...formData, protocol: e.target.value})}
                >
                  <option value="winrm">WinRM</option>
                  <option value="ssh">SSH</option>
                  <option value="http">HTTP</option>
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
                  onChange={(e) => setFormData({...formData, tags: e.target.value.split(',').map(t => t.trim()).filter(t => t)})}
                />
              </div>

              <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
                <button type="submit" className="btn btn-primary">Create Target</button>
                <button 
                  type="button" 
                  className="btn btn-secondary"
                  onClick={() => setShowCreateModal(false)}
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