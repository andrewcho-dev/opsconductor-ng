import React, { useState, useEffect } from 'react';
import { credentialApi } from '../services/api';
import { Credential, CredentialCreate } from '../types';

const Credentials: React.FC = () => {
  const [credentials, setCredentials] = useState<Credential[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [formData, setFormData] = useState<CredentialCreate>({
    name: '',
    description: '',
    credential_type: 'winrm',
    credential_data: {}
  });

  useEffect(() => {
    fetchCredentials();
  }, []);

  const fetchCredentials = async () => {
    try {
      const response = await credentialApi.list();
      setCredentials(response.credentials);
    } catch (error) {
      console.error('Failed to fetch credentials:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      // Build credential data based on type
      let credentialData: any = {};
      
      if (formData.credential_type === 'winrm') {
        const form = e.target as HTMLFormElement;
        const formDataObj = new FormData(form);
        credentialData = {
          username: formDataObj.get('username'),
          password: formDataObj.get('password'),
          domain: formDataObj.get('domain') || ''
        };
      }

      await credentialApi.create({
        ...formData,
        credential_data: credentialData
      });
      
      setShowCreateModal(false);
      setFormData({ name: '', description: '', credential_type: 'winrm', credential_data: {} });
      fetchCredentials();
    } catch (error) {
      console.error('Failed to create credential:', error);
    }
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this credential?')) {
      try {
        await credentialApi.delete(id);
        fetchCredentials();
      } catch (error) {
        console.error('Failed to delete credential:', error);
      }
    }
  };

  if (loading) return <div>Loading credentials...</div>;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h1>Credentials</h1>
        <button 
          className="btn btn-primary"
          onClick={() => setShowCreateModal(true)}
        >
          Add Credential
        </button>
      </div>

      <div className="card">
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Type</th>
              <th>Description</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {credentials.map(credential => (
              <tr key={credential.id}>
                <td>{credential.id}</td>
                <td>{credential.name}</td>
                <td>
                  <span className="status" style={{ 
                    backgroundColor: credential.credential_type === 'winrm' ? '#d4edda' : '#d1ecf1',
                    color: credential.credential_type === 'winrm' ? '#155724' : '#0c5460'
                  }}>
                    {credential.credential_type}
                  </span>
                </td>
                <td>{credential.description || '-'}</td>
                <td>{new Date(credential.created_at).toLocaleDateString()}</td>
                <td>
                  <button 
                    className="btn btn-danger"
                    onClick={() => handleDelete(credential.id)}
                    style={{ fontSize: '12px' }}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Create Credential Modal */}
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
            <h3>Add New Credential</h3>
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
                <label>Type:</label>
                <select 
                  value={formData.credential_type}
                  onChange={(e) => setFormData({...formData, credential_type: e.target.value})}
                >
                  <option value="winrm">WinRM</option>
                  <option value="ssh">SSH</option>
                  <option value="api_key">API Key</option>
                </select>
              </div>

              <div className="form-group">
                <label>Description:</label>
                <input
                  type="text"
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                />
              </div>

              {/* WinRM specific fields */}
              {formData.credential_type === 'winrm' && (
                <>
                  <div className="form-group">
                    <label>Username:</label>
                    <input
                      type="text"
                      name="username"
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label>Password:</label>
                    <input
                      type="password"
                      name="password"
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label>Domain (optional):</label>
                    <input
                      type="text"
                      name="domain"
                    />
                  </div>
                </>
              )}

              <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
                <button type="submit" className="btn btn-primary">Create Credential</button>
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

export default Credentials;