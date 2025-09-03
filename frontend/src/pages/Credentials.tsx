import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Plus, Trash2, Check, X } from 'lucide-react';
import { credentialApi } from '../services/api';
import { Credential, CredentialCreate, CredentialDecrypted } from '../types';

interface EditingState {
  credentialId: number;
  field: 'name' | 'description' | 'username' | 'password' | 'domain' | 'private_key' | 'passphrase';
  value: string;
  confirmPassword?: string;
}

interface NewCredentialState {
  name: string;
  description: string;
  credential_type: 'winrm' | 'ssh' | 'certificate';
  username: string;
  password: string;
  domain: string;
  private_key: string;
  passphrase: string;
  certificate: string;
  certificate_password: string;
}

const Credentials: React.FC = () => {
  const navigate = useNavigate();
  const { action, id } = useParams<{ action?: string; id?: string }>();
  const [credentials, setCredentials] = useState<CredentialDecrypted[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [editing, setEditing] = useState<EditingState | null>(null);
  const [addingNew, setAddingNew] = useState(false);
  const [selectedCredential, setSelectedCredential] = useState<CredentialDecrypted | null>(null);
  const [newCredential, setNewCredential] = useState<NewCredentialState>({
    name: '',
    description: '',
    credential_type: 'winrm',
    username: '',
    password: '',
    domain: '',
    private_key: '',
    passphrase: '',
    certificate: '',
    certificate_password: ''
  });

  useEffect(() => {
    fetchCredentials();
  }, []);

  const fetchCredentials = async () => {
    try {
      const response = await credentialApi.list();
      const basicCredentials = response.credentials || [];
      
      // Try to fetch decrypted data for each credential (admin/operator only)
      const credentialsWithData = await Promise.all(
        basicCredentials.map(async (cred) => {
          try {
            const decryptedCred = await credentialApi.getDecrypted(cred.id);
            return decryptedCred;
          } catch (error) {
            // If user doesn't have permission or other error, return basic credential
            return { ...cred, credential_data: {} };
          }
        })
      );
      
      setCredentials(credentialsWithData);
    } catch (error) {
      console.error('Failed to fetch credentials:', error);
      setCredentials([]);
    } finally {
      setLoading(false);
    }
  };

  const startAddingNew = () => {
    setAddingNew(true);
    setEditing(null);
  };

  const cancelAddingNew = () => {
    setAddingNew(false);
    setNewCredential({
      name: '',
      description: '',
      credential_type: 'winrm',
      username: '',
      password: '',
      domain: '',
      private_key: '',
      passphrase: '',
      certificate: '',
      certificate_password: ''
    });
  };

  const saveNewCredential = async () => {
    if (!newCredential.name.trim()) {
      alert('Name is required');
      return;
    }
    if (!newCredential.username.trim() && newCredential.credential_type !== 'certificate') {
      alert('Username is required');
      return;
    }
    if (!newCredential.password && newCredential.credential_type === 'winrm') {
      alert('Password is required for WinRM credentials');
      return;
    }
    if (!newCredential.private_key && newCredential.credential_type === 'ssh') {
      alert('Private key is required for SSH credentials');
      return;
    }
    if (!newCredential.certificate && newCredential.credential_type === 'certificate') {
      alert('Certificate is required');
      return;
    }

    try {
      setSaving(true);
      let credentialData: any = {};
      
      if (newCredential.credential_type === 'winrm') {
        credentialData = {
          username: newCredential.username,
          password: newCredential.password,
          domain: newCredential.domain || ''
        };
      } else if (newCredential.credential_type === 'ssh') {
        credentialData = {
          username: newCredential.username,
          private_key: newCredential.private_key
        };
        if (newCredential.passphrase) {
          credentialData.passphrase = newCredential.passphrase;
        }
      } else if (newCredential.credential_type === 'certificate') {
        credentialData = {
          certificate: newCredential.certificate
        };
        if (newCredential.certificate_password) {
          credentialData.certificate_password = newCredential.certificate_password;
        }
      }
      
      const credentialToCreate: CredentialCreate = {
        name: newCredential.name,
        description: newCredential.description,
        credential_type: newCredential.credential_type,
        credential_data: credentialData
      };
      
      await credentialApi.create(credentialToCreate);
      await fetchCredentials();
      cancelAddingNew();
    } catch (error) {
      console.error('Failed to create credential:', error);
      alert('Failed to create credential');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (credentialId: number) => {
    if (window.confirm('Delete this credential? This action cannot be undone.')) {
      try {
        await credentialApi.delete(credentialId);
        fetchCredentials();
        if (selectedCredential?.id === credentialId) {
          setSelectedCredential(null);
        }
      } catch (error) {
        console.error('Failed to delete credential:', error);
      }
    }
  };

  const startEditing = (credentialId: number, field: 'name' | 'description' | 'username' | 'password' | 'domain' | 'private_key' | 'passphrase', currentValue: string = '') => {
    setEditing({
      credentialId,
      field,
      value: field === 'password' || field === 'passphrase' ? '' : currentValue,
      confirmPassword: field === 'password' || field === 'passphrase' ? '' : undefined
    });
  };

  const cancelEditing = () => {
    setEditing(null);
  };

  const saveEdit = async () => {
    if (!editing) return;

    if (editing.field === 'password' || editing.field === 'passphrase') {
      if (!editing.value) {
        alert(`${editing.field} cannot be empty`);
        return;
      }
      if (editing.value !== editing.confirmPassword) {
        alert('Passwords do not match');
        return;
      }
      if (editing.value.length < 6) {
        alert(`${editing.field} must be at least 6 characters long`);
        return;
      }
    }

    if ((editing.field === 'name' || editing.field === 'username') && !editing.value.trim()) {
      alert(`${editing.field} cannot be empty`);
      return;
    }

    try {
      setSaving(true);
      const credential = credentials.find(c => c.id === editing.credentialId);
      if (!credential) return;

      let updateData: any = {};
      
      if (editing.field === 'name' || editing.field === 'description') {
        updateData[editing.field] = editing.value;
      } else {
        const newCredentialData = { ...credential.credential_data };
        newCredentialData[editing.field] = editing.value;
        updateData.credential_data = newCredentialData;
      }
      
      await credentialApi.update(editing.credentialId, updateData);
      await fetchCredentials();
      
      if (selectedCredential?.id === editing.credentialId) {
        if (editing.field === 'name' || editing.field === 'description') {
          setSelectedCredential({...selectedCredential, [editing.field]: editing.value});
        } else {
          const newCredData = { ...selectedCredential.credential_data };
          newCredData[editing.field] = editing.value;
          setSelectedCredential({...selectedCredential, credential_data: newCredData});
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

  const handleNewCredentialKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      saveNewCredential();
    } else if (e.key === 'Escape') {
      cancelAddingNew();
    }
  };

  const getCredentialTypeLabel = (type: string) => {
    switch (type) {
      case 'winrm': return 'WinRM';
      case 'ssh': return 'SSH';
      case 'certificate': return 'Certificate';
      default: return type.toUpperCase();
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
          
          /* Credentials table styles */
          .credentials-table-section {
            grid-column: 1 / 3;
          }
          .credentials-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
          }
          .credentials-table th {
            background: var(--neutral-50);
            padding: 6px 8px;
            text-align: left;
            font-weight: 600;
            color: var(--neutral-700);
            border-bottom: 1px solid var(--neutral-200);
            font-size: 11px;
          }
          .credentials-table td {
            padding: 6px 8px;
            border-bottom: 1px solid var(--neutral-100);
            vertical-align: middle;
            font-size: 12px;
          }
          .credentials-table tr:hover {
            background: var(--neutral-50);
          }
          .credentials-table tr.selected {
            background: var(--primary-blue-light);
            border-left: 3px solid var(--primary-blue);
          }
          .credentials-table tr {
            cursor: pointer;
          }
          
          /* Credential details panel */
          .credential-details {
            padding: 8px;
          }
          .credential-details h3 {
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
          .detail-value.editable {
            cursor: pointer;
            transition: background 0.2s;
          }
          .detail-value.editable:hover {
            background: var(--neutral-50);
            padding: 6px;
            margin: 0 -6px;
            border-radius: 3px;
          }
          
          /* Form styles */
          .detail-input {
            width: 100%;
            padding: 6px;
            border: 1px solid var(--neutral-300);
            border-radius: 3px;
            font-size: 12px;
          }
          .detail-input:focus {
            outline: none;
            border-color: var(--primary-blue);
            box-shadow: 0 0 0 2px var(--primary-blue-light);
          }
          .detail-textarea {
            width: 100%;
            padding: 6px;
            border: 1px solid var(--neutral-300);
            border-radius: 3px;
            font-size: 12px;
            resize: vertical;
            min-height: 60px;
          }
          .detail-textarea:focus {
            outline: none;
            border-color: var(--primary-blue);
            box-shadow: 0 0 0 2px var(--primary-blue-light);
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
          .status-badge-info {
            background: var(--primary-blue-light);
            color: var(--primary-blue);
          }
        `}
      </style>
      
      {/* Dashboard-style header */}
      <div className="dashboard-header">
        <div className="header-left">
          <h1>Credential Management</h1>
        </div>
        <div className="header-actions">
          <button 
            className="btn-icon btn-success"
            onClick={startAddingNew}
            title="Add new credential"
            disabled={addingNew}
          >
            <Plus size={16} />
          </button>
        </div>
      </div>

      {/* 3-column dashboard grid */}
      <div className="dashboard-grid">
        {/* Columns 1-2: Credentials Table */}
        <div className="dashboard-section credentials-table-section">
          <div className="section-header">
            Credentials ({credentials.length})
          </div>
          <div className="compact-content">
            {credentials.length === 0 && !addingNew ? (
              <div className="empty-state">
                <h3>No credentials found</h3>
                <p>Create your first credential to connect to targets.</p>
                <button 
                  className="btn-icon btn-success"
                  onClick={startAddingNew}
                  title="Create first credential"
                >
                  <Plus size={16} />
                </button>
              </div>
            ) : (
              <div className="table-container">
                <table className="credentials-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Type</th>
                    <th>Username</th>
                    <th>Domain</th>
                    <th>Description</th>
                    <th>Created</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {/* New Credential Row */}
                  {addingNew && (
                    <tr style={{ background: '#f0f9ff', border: '2px solid #10b981' }}>
                      <td>
                        <input
                          type="text"
                          value={newCredential.name}
                          onChange={(e) => setNewCredential({...newCredential, name: e.target.value})}
                          onKeyDown={handleNewCredentialKeyPress}
                          placeholder="Credential name"
                          style={{ width: '100%', border: 'none', background: 'transparent', padding: '4px' }}
                          autoFocus
                        />
                      </td>
                      <td>
                        <select 
                          value={newCredential.credential_type} 
                          onChange={(e) => setNewCredential({...newCredential, credential_type: e.target.value as any})}
                          style={{ width: '100%', border: 'none', background: 'transparent', padding: '4px' }}
                        >
                          <option value="winrm">WinRM</option>
                          <option value="ssh">SSH</option>
                          <option value="certificate">Certificate</option>
                        </select>
                      </td>
                      <td>
                        {newCredential.credential_type !== 'certificate' && (
                          <input
                            type="text"
                            value={newCredential.username}
                            onChange={(e) => setNewCredential({...newCredential, username: e.target.value})}
                            onKeyDown={handleNewCredentialKeyPress}
                            placeholder="Username"
                            style={{ width: '100%', border: 'none', background: 'transparent', padding: '4px' }}
                          />
                        )}
                      </td>
                      <td>
                        {newCredential.credential_type === 'winrm' && (
                          <input
                            type="text"
                            value={newCredential.domain}
                            onChange={(e) => setNewCredential({...newCredential, domain: e.target.value})}
                            onKeyDown={handleNewCredentialKeyPress}
                            placeholder="Domain (optional)"
                            style={{ width: '100%', border: 'none', background: 'transparent', padding: '4px' }}
                          />
                        )}
                      </td>
                      <td>
                        <input
                          type="text"
                          value={newCredential.description}
                          onChange={(e) => setNewCredential({...newCredential, description: e.target.value})}
                          onKeyDown={handleNewCredentialKeyPress}
                          placeholder="Description"
                          style={{ width: '100%', border: 'none', background: 'transparent', padding: '4px' }}
                        />
                      </td>
                      <td style={{ color: '#64748b', fontSize: '12px' }}>New</td>
                      <td>
                        <button onClick={saveNewCredential} className="btn-icon btn-success" title="Save" disabled={saving}>
                          <Check size={16} />
                        </button>
                        <button onClick={cancelAddingNew} className="btn-icon btn-ghost" title="Cancel">
                          <X size={16} />
                        </button>
                      </td>
                    </tr>
                  )}

                  {/* Existing Credentials */}
                  {credentials.map((credential) => (
                    <tr 
                      key={credential.id} 
                      className={selectedCredential?.id === credential.id ? 'selected' : ''}
                      onClick={() => setSelectedCredential(credential)}
                    >
                      <td style={{ fontWeight: '500' }}>{credential.name}</td>
                      <td>
                        <span className="status-badge status-badge-info">
                          {getCredentialTypeLabel(credential.credential_type)}
                        </span>
                      </td>
                      <td>{credential.credential_data?.username || '-'}</td>
                      <td>{credential.credential_data?.domain || (credential.credential_type === 'winrm' ? '-' : 'N/A')}</td>
                      <td>{credential.description || '-'}</td>
                      <td style={{ color: '#64748b', fontSize: '12px' }}>
                        {new Date(credential.created_at).toLocaleDateString()}
                      </td>
                      <td>
                        <button 
                          className="btn-icon btn-danger"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDelete(credential.id);
                          }}
                          title="Delete credential"
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

        {/* Column 3: Credential Details Panel */}
        <div className="dashboard-section">
          <div className="section-header">
            {selectedCredential ? `Credential Details` : 'Select Credential'}
          </div>
          <div className="compact-content">
            {selectedCredential ? (
              <div className="credential-details">
                <h3>{selectedCredential.name}</h3>
                
                <div className="detail-group">
                  <div className="detail-label">Name</div>
                  <div 
                    className="detail-value editable"
                    onClick={() => startEditing(selectedCredential.id, 'name', selectedCredential.name)}
                  >
                    {editing?.credentialId === selectedCredential.id && editing?.field === 'name' ? (
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
                      selectedCredential.name
                    )}
                  </div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">Type</div>
                  <div className="detail-value">
                    <span className="status-badge status-badge-info">
                      {getCredentialTypeLabel(selectedCredential.credential_type)}
                    </span>
                  </div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">Description</div>
                  <div 
                    className="detail-value editable"
                    onClick={() => startEditing(selectedCredential.id, 'description', selectedCredential.description || '')}
                  >
                    {editing?.credentialId === selectedCredential.id && editing?.field === 'description' ? (
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
                      selectedCredential.description || '-'
                    )}
                  </div>
                </div>

                {selectedCredential.credential_type !== 'certificate' && (
                  <div className="detail-group">
                    <div className="detail-label">Username</div>
                    <div 
                      className="detail-value editable"
                      onClick={() => startEditing(selectedCredential.id, 'username', selectedCredential.credential_data?.username || '')}
                    >
                      {editing?.credentialId === selectedCredential.id && editing?.field === 'username' ? (
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
                        selectedCredential.credential_data?.username || '-'
                      )}
                    </div>
                  </div>
                )}

                {selectedCredential.credential_type === 'winrm' && (
                  <>
                    <div className="detail-group">
                      <div className="detail-label">Domain</div>
                      <div 
                        className="detail-value editable"
                        onClick={() => startEditing(selectedCredential.id, 'domain', selectedCredential.credential_data?.domain || '')}
                      >
                        {editing?.credentialId === selectedCredential.id && editing?.field === 'domain' ? (
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
                          selectedCredential.credential_data?.domain || '-'
                        )}
                      </div>
                    </div>

                    <div className="detail-group">
                      <div className="detail-label">Password</div>
                      <div 
                        className="detail-value editable"
                        onClick={() => startEditing(selectedCredential.id, 'password')}
                      >
                        {editing?.credentialId === selectedCredential.id && editing?.field === 'password' ? (
                          <div>
                            <input
                              type="password"
                              placeholder="New password"
                              value={editing.value}
                              onChange={(e) => setEditing({...editing, value: e.target.value})}
                              onKeyDown={handleKeyPress}
                              className="detail-input"
                              autoFocus
                            />
                            <input
                              type="password"
                              placeholder="Confirm password"
                              value={editing.confirmPassword || ''}
                              onChange={(e) => setEditing({...editing, confirmPassword: e.target.value})}
                              onKeyDown={handleKeyPress}
                              className="detail-input"
                              style={{ marginTop: '6px' }}
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
                          '••••••••'
                        )}
                      </div>
                    </div>
                  </>
                )}

                {selectedCredential.credential_type === 'ssh' && (
                  <>
                    <div className="detail-group">
                      <div className="detail-label">Private Key</div>
                      <div 
                        className="detail-value editable"
                        onClick={() => startEditing(selectedCredential.id, 'private_key', selectedCredential.credential_data?.private_key || '')}
                      >
                        {editing?.credentialId === selectedCredential.id && editing?.field === 'private_key' ? (
                          <div>
                            <textarea
                              value={editing.value}
                              onChange={(e) => setEditing({...editing, value: e.target.value})}
                              onKeyDown={handleKeyPress}
                              className="detail-textarea"
                              placeholder="-----BEGIN PRIVATE KEY-----"
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
                          selectedCredential.credential_data?.private_key ? '••••••••' : '-'
                        )}
                      </div>
                    </div>

                    <div className="detail-group">
                      <div className="detail-label">Passphrase</div>
                      <div 
                        className="detail-value editable"
                        onClick={() => startEditing(selectedCredential.id, 'passphrase')}
                      >
                        {editing?.credentialId === selectedCredential.id && editing?.field === 'passphrase' ? (
                          <div>
                            <input
                              type="password"
                              placeholder="New passphrase"
                              value={editing.value}
                              onChange={(e) => setEditing({...editing, value: e.target.value})}
                              onKeyDown={handleKeyPress}
                              className="detail-input"
                              autoFocus
                            />
                            <input
                              type="password"
                              placeholder="Confirm passphrase"
                              value={editing.confirmPassword || ''}
                              onChange={(e) => setEditing({...editing, confirmPassword: e.target.value})}
                              onKeyDown={handleKeyPress}
                              className="detail-input"
                              style={{ marginTop: '6px' }}
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
                          selectedCredential.credential_data?.passphrase ? '••••••••' : '-'
                        )}
                      </div>
                    </div>
                  </>
                )}

                <div className="detail-group">
                  <div className="detail-label">Created</div>
                  <div className="detail-value">
                    {new Date(selectedCredential.created_at).toLocaleString()}
                  </div>
                </div>

                <div className="action-buttons">
                  <button 
                    className="btn-icon btn-danger"
                    onClick={() => handleDelete(selectedCredential.id)}
                    title="Delete credential"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            ) : (
              <div className="empty-state">
                <p>Select a credential from the table to view and edit details</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Credentials;