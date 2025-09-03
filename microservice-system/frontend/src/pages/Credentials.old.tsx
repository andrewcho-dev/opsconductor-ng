import React, { useState, useEffect } from 'react';
import { credentialApi } from '../services/api';
import { Credential, CredentialCreate } from '../types';

const Credentials: React.FC = () => {
  const [credentials, setCredentials] = useState<Credential[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingCredential, setEditingCredential] = useState<Credential | null>(null);
  const [editingCredentialData, setEditingCredentialData] = useState<Record<string, any>>({});
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
      setCredentials(response.credentials || []);
    } catch (error) {
      console.error('Failed to fetch credentials:', error);
      setCredentials([]); // Set empty array on error
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
          domain: formDataObj.get('domain') || ''
        };
        
        // Only include password if it's provided (for updates, empty means keep current)
        const password = formDataObj.get('password') as string;
        if (password || !editingCredential) {
          credentialData.password = password;
        }
      } else if (formData.credential_type === 'ssh') {
        const form = e.target as HTMLFormElement;
        const formDataObj = new FormData(form);
        credentialData = {
          username: formDataObj.get('username'),
          port: parseInt(formDataObj.get('port') as string) || 22,
          timeout: parseInt(formDataObj.get('timeout') as string) || 30
        };
        
        // Only include password if it's provided (for updates, empty means keep current)
        const password = formDataObj.get('password') as string;
        if (password || !editingCredential) {
          credentialData.password = password;
        }
      } else if (formData.credential_type === 'ssh_key') {
        const form = e.target as HTMLFormElement;
        const formDataObj = new FormData(form);
        credentialData = {
          username: formDataObj.get('username'),
          key_type: formDataObj.get('key_type') || 'rsa'
        };
        
        // Only include private_key if it's provided (for updates, empty means keep current)
        const privateKey = formDataObj.get('private_key') as string;
        if (privateKey || !editingCredential) {
          credentialData.private_key = privateKey;
        }
        
        // Only include passphrase if it's provided
        const passphrase = formDataObj.get('passphrase') as string;
        if (passphrase) {
          credentialData.passphrase = passphrase;
        }
      }

      if (editingCredential) {
        await credentialApi.update(editingCredential.id, {
          ...formData,
          credential_data: credentialData
        });
      } else {
        await credentialApi.create({
          ...formData,
          credential_data: credentialData
        });
      }
      
      setShowCreateModal(false);
      setEditingCredential(null);
      setEditingCredentialData({});
      setFormData({ name: '', description: '', credential_type: 'winrm', credential_data: {} });
      fetchCredentials();
    } catch (error) {
      console.error(`Failed to ${editingCredential ? 'update' : 'create'} credential:`, error);
    }
  };

  const resetForm = () => {
    setFormData({ 
      name: '', 
      description: '', 
      credential_type: 'winrm', 
      credential_data: {} 
    });
    setEditingCredential(null);
    setEditingCredentialData({});
  };

  const handleEdit = async (credential: Credential) => {
    setEditingCredential(credential);
    setFormData({
      name: credential.name,
      description: credential.description || '',
      credential_type: credential.credential_type,
      credential_data: {} // Don't pre-fill credential data for security
    });
    
    // Fetch the decrypted credential data to prepopulate form fields
    try {
      const decryptedCred = await credentialApi.getDecrypted(credential.id);
      setEditingCredentialData(decryptedCred.credential_data);
    } catch (error) {
      console.error('Failed to fetch credential data:', error);
      setEditingCredentialData({});
    }
    
    setShowCreateModal(true);
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
          onClick={() => {
            resetForm();
            setShowCreateModal(true);
          }}
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
            {(credentials || []).map(credential => (
              <tr key={credential.id}>
                <td>{credential.id}</td>
                <td>{credential.name}</td>
                <td>
                  <span className="status" style={{ 
                    backgroundColor: 
                      credential.credential_type === 'winrm' ? '#d4edda' : 
                      credential.credential_type === 'ssh' ? '#fff3cd' :
                      credential.credential_type === 'ssh_key' ? '#f8d7da' :
                      '#d1ecf1',
                    color: 
                      credential.credential_type === 'winrm' ? '#155724' : 
                      credential.credential_type === 'ssh' ? '#856404' :
                      credential.credential_type === 'ssh_key' ? '#721c24' :
                      '#0c5460'
                  }}>
                    {credential.credential_type}
                  </span>
                </td>
                <td>{credential.description || '-'}</td>
                <td>{new Date(credential.created_at).toLocaleDateString()}</td>
                <td>
                  <div style={{ display: 'flex', gap: '5px' }}>
                    <button 
                      className="btn btn-secondary"
                      onClick={() => handleEdit(credential)}
                      style={{ fontSize: '12px' }}
                    >
                      Edit
                    </button>
                    <button 
                      className="btn btn-danger"
                      onClick={() => handleDelete(credential.id)}
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
            <h3>{editingCredential ? 'Edit Credential' : 'Add New Credential'}</h3>
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
                  <option value="ssh">SSH Password</option>
                  <option value="ssh_key">SSH Key</option>
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
                      defaultValue={editingCredentialData.username || ''}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label>Password{editingCredential ? ' (leave blank to keep current)' : ''}:</label>
                    <input
                      type="password"
                      name="password"
                      required={!editingCredential}
                    />
                  </div>
                  <div className="form-group">
                    <label>Domain (optional):</label>
                    <input
                      type="text"
                      name="domain"
                      defaultValue={editingCredentialData.domain || ''}
                    />
                  </div>
                </>
              )}

              {/* SSH Password specific fields */}
              {formData.credential_type === 'ssh' && (
                <>
                  <div className="form-group">
                    <label>Username:</label>
                    <input
                      type="text"
                      name="username"
                      defaultValue={editingCredentialData.username || ''}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label>Password{editingCredential ? ' (leave blank to keep current)' : ''}:</label>
                    <input
                      type="password"
                      name="password"
                      required={!editingCredential}
                    />
                  </div>
                  <div className="form-group">
                    <label>SSH Port:</label>
                    <input
                      type="number"
                      name="port"
                      defaultValue={editingCredentialData.port || 22}
                      min="1"
                      max="65535"
                    />
                  </div>
                  <div className="form-group">
                    <label>Timeout (seconds):</label>
                    <input
                      type="number"
                      name="timeout"
                      defaultValue={editingCredentialData.timeout || 30}
                      min="5"
                      max="300"
                    />
                  </div>
                </>
              )}

              {/* SSH Key specific fields */}
              {formData.credential_type === 'ssh_key' && (
                <>
                  <div className="form-group">
                    <label>Username:</label>
                    <input
                      type="text"
                      name="username"
                      defaultValue={editingCredentialData.username || ''}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label>Private Key{editingCredential ? ' (leave blank to keep current)' : ''}:</label>
                    <textarea
                      name="private_key"
                      rows={8}
                      placeholder={editingCredential ? "Leave blank to keep current key" : "-----BEGIN OPENSSH PRIVATE KEY-----\n...\n-----END OPENSSH PRIVATE KEY-----"}
                      style={{ fontFamily: 'monospace', fontSize: '12px' }}
                      required={!editingCredential}
                    />
                    <small style={{ color: '#666' }}>
                      {editingCredential ? 'Leave blank to keep current private key' : 'Paste your SSH private key in OpenSSH format'}
                    </small>
                  </div>
                  <div className="form-group">
                    <label>Key Type:</label>
                    <select name="key_type" defaultValue={editingCredentialData.key_type || 'rsa'}>
                      <option value="rsa">RSA</option>
                      <option value="ed25519">Ed25519</option>
                      <option value="ecdsa">ECDSA</option>
                      <option value="dsa">DSA</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label>Passphrase (optional):</label>
                    <input
                      type="password"
                      name="passphrase"
                      placeholder={editingCredential ? "Leave empty to keep current passphrase" : "Leave empty if key is not encrypted"}
                    />
                  </div>
                </>
              )}

              <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
                <button type="submit" className="btn btn-primary">
                  {editingCredential ? 'Update Credential' : 'Create Credential'}
                </button>
                <button 
                  type="button" 
                  className="btn btn-secondary"
                  onClick={() => {
                    setShowCreateModal(false);
                    setEditingCredential(null);
                    setEditingCredentialData({});
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

export default Credentials;