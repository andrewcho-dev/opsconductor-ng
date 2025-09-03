import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { credentialApi } from '../services/api';
import { Credential, CredentialCreate, CredentialDecrypted } from '../types';
import { Plus, Trash2, Check, X } from 'lucide-react';

interface EditingState {
  credentialId: number;
  field: 'name' | 'description' | 'username' | 'password' | 'domain' | 'private_key' | 'passphrase';
  value: string;
  confirmPassword?: string;
}

const Credentials: React.FC = () => {
  const navigate = useNavigate();
  const { action, id } = useParams<{ action?: string; id?: string }>();
  const [credentials, setCredentials] = useState<CredentialDecrypted[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [editing, setEditing] = useState<EditingState | null>(null);
  const [showSlideOut, setShowSlideOut] = useState(false);
  const [slideOutMode, setSlideOutMode] = useState<'create' | 'edit'>('create');
  const [selectedCredential, setSelectedCredential] = useState<CredentialDecrypted | null>(null);
  const [formData, setFormData] = useState<CredentialCreate>({
    name: '',
    description: '',
    credential_type: 'winrm',
    credential_data: {}
  });
  const [credentialFields, setCredentialFields] = useState<Record<string, string>>({
    username: '',
    password: '',
    domain: '',
    private_key: '',
    passphrase: '',
    certificate: '',
    certificate_password: ''
  });

  const isCreating = action === 'create';
  const showForm = isCreating;

  useEffect(() => {
    fetchCredentials();
  }, []);

  useEffect(() => {
    if (isCreating) {
      setFormData({
        name: '',
        description: '',
        credential_type: 'winrm',
        credential_data: {}
      });
      setCredentialFields({
        username: '',
        password: '',
        domain: '',
        private_key: '',
        passphrase: ''
      });
    }
  }, [isCreating]);

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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    
    try {
      let credentialData: any = {};
      
      if (formData.credential_type === 'winrm') {
        credentialData = {
          username: credentialFields.username,
          domain: credentialFields.domain || ''
        };
        if (credentialFields.password) {
          credentialData.password = credentialFields.password;
        }
      } else if (formData.credential_type === 'ssh') {
        credentialData = {
          username: credentialFields.username
        };
        if (credentialFields.password) {
          credentialData.password = credentialFields.password;
        }
        if (credentialFields.private_key) {
          credentialData.private_key = credentialFields.private_key;
        }
        if (credentialFields.passphrase) {
          credentialData.passphrase = credentialFields.passphrase;
        }
      }

      const submitData = {
        ...formData,
        credential_data: credentialData
      };

      await credentialApi.create(submitData);
      await fetchCredentials();
      navigate('/credential-management');
    } catch (error) {
      console.error('Failed to create credential:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (credentialId: number) => {
    if (window.confirm('Delete this credential? This action cannot be undone.')) {
      try {
        await credentialApi.delete(credentialId);
        fetchCredentials();
      } catch (error) {
        console.error('Failed to delete credential:', error);
      }
    }
  };

  const handleTypeChange = (type: string) => {
    setFormData({ ...formData, credential_type: type });
    // Reset credential fields when type changes
    setCredentialFields({
      username: '',
      password: '',
      domain: '',
      private_key: '',
      passphrase: ''
    });
  };

  const getCredentialTypeLabel = (type: string) => {
    switch (type) {
      case 'winrm': return 'WinRM';
      case 'ssh': return 'SSH';
      default: return type.toUpperCase();
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

    // Password validation
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

    // Other field validation
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
        // Update basic credential fields
        updateData[editing.field] = editing.value;
      } else {
        // Update credential_data fields
        const newCredentialData = { ...credential.credential_data };
        newCredentialData[editing.field] = editing.value;
        updateData.credential_data = newCredentialData;
      }
      
      await credentialApi.update(editing.credentialId, updateData);
      await fetchCredentials();
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

  const openCreateSlideOut = () => {
    setSlideOutMode('create');
    setSelectedCredential(null);
    setFormData({
      name: '',
      description: '',
      credential_type: 'winrm',
      credential_data: {}
    });
    setCredentialFields({
      username: '',
      password: '',
      domain: '',
      private_key: '',
      passphrase: ''
    });
    setShowSlideOut(true);
  };

  const openEditSlideOut = (credential: CredentialDecrypted) => {
    setSlideOutMode('edit');
    setSelectedCredential(credential);
    setFormData({
      name: credential.name,
      description: credential.description || '',
      credential_type: credential.credential_type,
      credential_data: credential.credential_data
    });
    setCredentialFields({
      username: credential.credential_data.username || '',
      password: '',
      domain: credential.credential_data.domain || '',
      private_key: credential.credential_data.private_key || '',
      passphrase: '',
      certificate: credential.credential_data.certificate || '',
      certificate_password: ''
    });
    setShowSlideOut(true);
  };

  const closeSlideOut = () => {
    setShowSlideOut(false);
    setSelectedCredential(null);
  };

  const handleCertificateFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      const text = await file.text();
      setCredentialFields({...credentialFields, certificate: text});
    } catch (error) {
      console.error('Error reading certificate file:', error);
      alert('Error reading certificate file. Please try again.');
    }
  };

  const handleSlideOutSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.name.trim()) {
      alert('Name is required');
      return;
    }
    
    // Validate based on credential type
    if (formData.credential_type === 'winrm') {
      if (!credentialFields.username.trim()) {
        alert('Username is required');
        return;
      }
      if (slideOutMode === 'create' && !credentialFields.password.trim()) {
        alert('Password is required');
        return;
      }
    } else if (formData.credential_type === 'ssh') {
      if (!credentialFields.username.trim()) {
        alert('Username is required');
        return;
      }
      if (slideOutMode === 'create' && !credentialFields.private_key.trim()) {
        alert('Private key is required');
        return;
      }
    } else if (formData.credential_type === 'certificate') {
      if (slideOutMode === 'create' && !credentialFields.certificate.trim()) {
        alert('Certificate is required');
        return;
      }
    }

    setSaving(true);
    try {
      let credentialData: any = {};
      
      if (formData.credential_type === 'winrm') {
        credentialData.username = credentialFields.username;
        if (credentialFields.password.trim()) {
          credentialData.password = credentialFields.password;
        }
        if (credentialFields.domain.trim()) {
          credentialData.domain = credentialFields.domain;
        }
      } else if (formData.credential_type === 'ssh') {
        credentialData.username = credentialFields.username;
        if (credentialFields.private_key.trim()) {
          credentialData.private_key = credentialFields.private_key;
        }
        if (credentialFields.passphrase.trim()) {
          credentialData.passphrase = credentialFields.passphrase;
        }
      } else if (formData.credential_type === 'certificate') {
        credentialData.certificate = credentialFields.certificate;
        if (credentialFields.certificate_password.trim()) {
          credentialData.certificate_password = credentialFields.certificate_password;
        }
      }

      const credentialToSave: CredentialCreate = {
        name: formData.name,
        description: formData.description || '',
        credential_type: formData.credential_type,
        credential_data: credentialData
      };

      if (slideOutMode === 'create') {
        await credentialApi.create(credentialToSave);
      } else if (selectedCredential) {
        await credentialApi.update(selectedCredential.id, credentialToSave);
      }
      
      await fetchCredentials();
      closeSlideOut();
    } catch (error) {
      console.error('Failed to save credential:', error);
      alert('Failed to save credential');
    } finally {
      setSaving(false);
    }
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
          <h1 className="page-title">Create Credential</h1>
          <div className="page-actions">
            <button 
              type="button" 
              className="btn btn-ghost"
              onClick={() => navigate('/credential-management')}
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
                <label className="form-label">Type</label>
                <select 
                  className="form-select"
                  value={formData.credential_type}
                  onChange={(e) => handleTypeChange(e.target.value)}
                >
                  <option value="winrm">WinRM</option>
                  <option value="ssh">SSH</option>
                </select>
              </div>

              <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                <label className="form-label">Description</label>
                <textarea
                  className="form-textarea"
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  rows={2}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Username</label>
                <input
                  type="text"
                  className="form-input"
                  value={credentialFields.username}
                  onChange={(e) => setCredentialFields({...credentialFields, username: e.target.value})}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Password</label>
                <input
                  type="password"
                  className="form-input"
                  value={credentialFields.password}
                  onChange={(e) => setCredentialFields({...credentialFields, password: e.target.value})}
                  required
                />
              </div>

              {formData.credential_type === 'winrm' && (
                <div className="form-group">
                  <label className="form-label">Domain</label>
                  <input
                    type="text"
                    className="form-input"
                    value={credentialFields.domain}
                    onChange={(e) => setCredentialFields({...credentialFields, domain: e.target.value})}
                    placeholder="Optional"
                  />
                </div>
              )}

              {formData.credential_type === 'ssh' && (
                <>
                  <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                    <label className="form-label">Private Key (Optional)</label>
                    <textarea
                      className="form-textarea"
                      value={credentialFields.private_key}
                      onChange={(e) => setCredentialFields({...credentialFields, private_key: e.target.value})}
                      rows={4}
                      placeholder="-----BEGIN PRIVATE KEY-----"
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Passphrase (Optional)</label>
                    <input
                      type="password"
                      className="form-input"
                      value={credentialFields.passphrase}
                      onChange={(e) => setCredentialFields({...credentialFields, passphrase: e.target.value})}
                      placeholder="For encrypted private keys"
                    />
                  </div>
                </>
              )}
            </div>

            <div className="form-actions">
              <button 
                type="button" 
                className="btn btn-ghost"
                onClick={() => navigate('/credential-management')}
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
                    Creating...
                  </>
                ) : (
                  'Create Credential'
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
          .btn-icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 32px;
            height: 32px;
            border: none;
            background: none;
            cursor: pointer;
            transition: all 0.2s;
            margin: 0 2px;
            padding: 4px;
          }
          .btn-icon:hover {
            opacity: 0.7;
          }
          .btn-icon:disabled {
            opacity: 0.3;
            cursor: not-allowed;
          }
          .btn-success {
            color: #10b981;
          }
          .btn-success:hover:not(:disabled) {
            color: #059669;
          }
          .btn-danger {
            color: #ef4444;
          }
          .btn-danger:hover:not(:disabled) {
            color: #dc2626;
          }
          .btn-ghost {
            color: #6b7280;
          }
          .btn-ghost:hover:not(:disabled) {
            color: #374151;
          }
          .new-credential-row .table-input {
            border: none;
            background: transparent;
            padding: 4px 2px;
            font-size: 13px;
            width: 100%;
            min-width: 80px;
            outline: none;
          }
          .new-credential-row .table-input:focus {
            background: white;
            border: 1px solid #10b981;
            border-radius: 2px;
            box-shadow: none;
          }
          .new-credential-row .table-input::placeholder {
            color: #9ca3af;
            font-size: 12px;
          }
          .slide-out-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            z-index: 1000;
            display: flex;
            justify-content: flex-end;
          }
          .slide-out-panel {
            background: white;
            width: 500px;
            height: 100vh;
            box-shadow: -2px 0 10px rgba(0, 0, 0, 0.1);
            display: flex;
            flex-direction: column;
            animation: slideIn 0.3s ease-out;
          }
          @keyframes slideIn {
            from { transform: translateX(100%); }
            to { transform: translateX(0); }
          }
          .slide-out-header {
            padding: 20px;
            border-bottom: 1px solid #e5e7eb;
            display: flex;
            justify-content: space-between;
            align-items: center;
          }
          .slide-out-header h2 {
            margin: 0;
            font-size: 18px;
            font-weight: 600;
          }
          .slide-out-content {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
          }
          .slide-out-actions {
            padding: 20px;
            border-top: 1px solid #e5e7eb;
            display: flex;
            gap: 12px;
            justify-content: flex-end;
          }
          .certificate-input-container {
            display: flex;
            flex-direction: column;
            gap: 16px;
          }
          .certificate-upload-section {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 8px;
            padding: 16px;
            border: 2px dashed #d1d5db;
            border-radius: 8px;
            background: #f9fafb;
          }
          .upload-divider {
            position: relative;
            text-align: center;
            color: #6b7280;
            font-size: 12px;
            font-weight: 500;
            margin-bottom: 8px;
          }
          .upload-divider::before {
            content: '';
            position: absolute;
            top: 50%;
            left: -20px;
            right: -20px;
            height: 1px;
            background: #d1d5db;
            z-index: 1;
          }
          .upload-divider span {
            background: #f9fafb;
            padding: 0 8px;
            position: relative;
            z-index: 2;
          }
          .file-input {
            display: none;
          }
          .form-help {
            color: #6b7280;
            font-size: 12px;
            text-align: center;
            margin: 0;
          }
        `}
      </style>
      <div className="page-header">
        <h1 className="page-title">Credentials</h1>
        <div className="page-actions">
          <button 
            className="btn-icon btn-success"
            onClick={openCreateSlideOut}
            title="Add new credential"
          >
            <Plus size={16} />
          </button>
        </div>
      </div>

      {credentials.length === 0 ? (
        <div className="empty-state">
          <h3 className="empty-state-title">No credentials found</h3>
          <p className="empty-state-description">
            Create your first credential to connect to targets.
          </p>
          <button 
            className="btn-icon btn-success"
            onClick={openCreateSlideOut}
            title="Create first credential"
          >
            <Plus size={16} />
          </button>
        </div>
      ) : (
        <div className="data-table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Type</th>
                <th>Username</th>
                <th>Domain</th>
                <th>Password</th>
                <th>Description</th>
                <th>Created</th>
                <th className="text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {credentials.map(credential => (
                <tr key={credential.id}>
                  <td className="text-neutral-500">{credential.id}</td>
                  
                  {/* Name - Inline Editable */}
                  <td className="font-medium">
                    {editing?.credentialId === credential.id && editing?.field === 'name' ? (
                      <div className="inline-edit">
                        <input
                          type="text"
                          value={editing.value}
                          onChange={(e) => setEditing({...editing, value: e.target.value})}
                          onKeyDown={handleKeyPress}
                          className="table-input"
                          autoFocus
                        />
                        <div className="inline-edit-actions">
                          <button onClick={saveEdit} className="btn-icon btn-success" title="Save" disabled={saving}>
                            <Check size={16} />
                          </button>
                          <button onClick={cancelEditing} className="btn-icon btn-ghost" title="Cancel">
                            <X size={16} />
                          </button>
                        </div>
                      </div>
                    ) : (
                      <span 
                        onClick={() => startEditing(credential.id, 'name', credential.name)}
                        className="editable-field"
                        title="Click to edit name"
                      >
                        {credential.name}
                      </span>
                    )}
                  </td>

                  {/* Type - Not editable for security reasons */}
                  <td>
                    <span className="status-badge status-badge-info">
                      {getCredentialTypeLabel(credential.credential_type)}
                    </span>
                  </td>

                  {/* Username - Inline Editable */}
                  <td>
                    {editing?.credentialId === credential.id && editing?.field === 'username' ? (
                      <div className="inline-edit">
                        <input
                          type="text"
                          value={editing.value}
                          onChange={(e) => setEditing({...editing, value: e.target.value})}
                          onKeyDown={handleKeyPress}
                          className="table-input"
                          autoFocus
                        />
                        <div className="inline-edit-actions">
                          <button onClick={saveEdit} className="btn-icon btn-success" title="Save" disabled={saving}>
                            <Check size={16} />
                          </button>
                          <button onClick={cancelEditing} className="btn-icon btn-ghost" title="Cancel">
                            <X size={16} />
                          </button>
                        </div>
                      </div>
                    ) : (
                      <span 
                        onClick={() => startEditing(credential.id, 'username', credential.credential_data?.username || '')}
                        className="editable-field"
                        title="Click to edit username"
                      >
                        {credential.credential_data?.username || <span className="text-neutral-400">-</span>}
                      </span>
                    )}
                  </td>

                  {/* Domain - Inline Editable (WinRM only) */}
                  <td>
                    {credential.credential_type === 'winrm' ? (
                      editing?.credentialId === credential.id && editing?.field === 'domain' ? (
                        <div className="inline-edit">
                          <input
                            type="text"
                            value={editing.value}
                            onChange={(e) => setEditing({...editing, value: e.target.value})}
                            onKeyDown={handleKeyPress}
                            className="table-input"
                            autoFocus
                          />
                          <div className="inline-edit-actions">
                            <button onClick={saveEdit} className="btn-icon btn-success" title="Save" disabled={saving}>
                              <Check size={14} />
                            </button>
                            <button onClick={cancelEditing} className="btn-icon btn-ghost" title="Cancel">
                              <X size={14} />
                            </button>
                          </div>
                        </div>
                      ) : (
                        <span 
                          onClick={() => startEditing(credential.id, 'domain', credential.credential_data?.domain || '')}
                          className="editable-field"
                          title="Click to edit domain"
                        >
                          {credential.credential_data?.domain || <span className="text-neutral-400">-</span>}
                        </span>
                      )
                    ) : (
                      <span className="text-neutral-400">N/A</span>
                    )}
                  </td>

                  {/* Password - Inline Editable with Confirmation */}
                  <td>
                    {editing?.credentialId === credential.id && editing?.field === 'password' ? (
                      <div className="inline-edit password-edit">
                        <div className="password-inputs">
                          <input
                            type="password"
                            placeholder="New password"
                            value={editing.value}
                            onChange={(e) => setEditing({...editing, value: e.target.value})}
                            onKeyDown={handleKeyPress}
                            className="table-input"
                            autoFocus
                          />
                          <input
                            type="password"
                            placeholder="Confirm password"
                            value={editing.confirmPassword || ''}
                            onChange={(e) => setEditing({...editing, confirmPassword: e.target.value})}
                            onKeyDown={handleKeyPress}
                            className="table-input"
                          />
                        </div>
                        <div className="inline-edit-actions">
                          <button onClick={saveEdit} className="btn-icon btn-success" title="Save" disabled={saving}>
                            <Check size={16} />
                          </button>
                          <button onClick={cancelEditing} className="btn-icon btn-ghost" title="Cancel">
                            <X size={16} />
                          </button>
                        </div>
                      </div>
                    ) : (
                      <span 
                        onClick={() => startEditing(credential.id, 'password')}
                        className="editable-field password-field"
                        title="Click to change password"
                      >
                        ••••••••
                      </span>
                    )}
                  </td>

                  {/* Description - Inline Editable */}
                  <td>
                    {editing?.credentialId === credential.id && editing?.field === 'description' ? (
                      <div className="inline-edit">
                        <input
                          type="text"
                          value={editing.value}
                          onChange={(e) => setEditing({...editing, value: e.target.value})}
                          onKeyDown={handleKeyPress}
                          className="table-input"
                          autoFocus
                        />
                        <div className="inline-edit-actions">
                          <button onClick={saveEdit} className="btn-icon btn-success" title="Save" disabled={saving}>
                            <Check size={16} />
                          </button>
                          <button onClick={cancelEditing} className="btn-icon btn-ghost" title="Cancel">
                            <X size={16} />
                          </button>
                        </div>
                      </div>
                    ) : (
                      <span 
                        onClick={() => startEditing(credential.id, 'description', credential.description || '')}
                        className="editable-field"
                        title="Click to edit description"
                      >
                        {credential.description || <span className="text-neutral-400">-</span>}
                      </span>
                    )}
                  </td>

                  <td className="text-neutral-500">
                    {new Date(credential.created_at).toLocaleDateString()}
                  </td>

                  {/* Actions - Only Delete Now */}
                  <td>
                    <div className="table-actions">
                      <button 
                        className="btn-icon btn-danger"
                        onClick={() => handleDelete(credential.id)}
                        title="Delete credential"
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

      {/* Slide-out Panel */}
      {showSlideOut && (
        <div className="slide-out-overlay" onClick={closeSlideOut}>
          <div className="slide-out-panel" onClick={(e) => e.stopPropagation()}>
            <div className="slide-out-header">
              <h2>{slideOutMode === 'create' ? 'Create Credential' : 'Edit Credential'}</h2>
              <button onClick={closeSlideOut} className="btn-icon btn-ghost">
                <X size={20} />
              </button>
            </div>
            
            <div className="slide-out-content">
              <form onSubmit={handleSlideOutSubmit}>
                <div className="form-group">
                  <label className="form-label">Name</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    className="form-input"
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Type</label>
                  <select
                    value={formData.credential_type}
                    onChange={(e) => setFormData({...formData, credential_type: e.target.value as 'winrm' | 'ssh' | 'certificate'})}
                    className="form-select"
                  >
                    <option value="winrm">Username/Password</option>
                    <option value="ssh">SSH Key</option>
                    <option value="certificate">Certificate</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Description</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({...formData, description: e.target.value})}
                    className="form-textarea"
                    rows={3}
                  />
                </div>

                {/* Username/Password Fields */}
                {formData.credential_type === 'winrm' && (
                  <>
                    <div className="form-group">
                      <label className="form-label">Username</label>
                      <input
                        type="text"
                        value={credentialFields.username}
                        onChange={(e) => setCredentialFields({...credentialFields, username: e.target.value})}
                        className="form-input"
                        required
                      />
                    </div>

                    <div className="form-group">
                      <label className="form-label">Password</label>
                      <input
                        type="password"
                        value={credentialFields.password}
                        onChange={(e) => setCredentialFields({...credentialFields, password: e.target.value})}
                        className="form-input"
                        required={slideOutMode === 'create'}
                        placeholder={slideOutMode === 'edit' ? 'Leave blank to keep current password' : ''}
                      />
                    </div>

                    <div className="form-group">
                      <label className="form-label">Domain (Optional)</label>
                      <input
                        type="text"
                        value={credentialFields.domain}
                        onChange={(e) => setCredentialFields({...credentialFields, domain: e.target.value})}
                        className="form-input"
                      />
                    </div>
                  </>
                )}

                {/* SSH Key Fields */}
                {formData.credential_type === 'ssh' && (
                  <>
                    <div className="form-group">
                      <label className="form-label">Username</label>
                      <input
                        type="text"
                        value={credentialFields.username}
                        onChange={(e) => setCredentialFields({...credentialFields, username: e.target.value})}
                        className="form-input"
                        required
                      />
                    </div>

                    <div className="form-group">
                      <label className="form-label">Private Key</label>
                      <textarea
                        value={credentialFields.private_key}
                        onChange={(e) => setCredentialFields({...credentialFields, private_key: e.target.value})}
                        className="form-textarea"
                        rows={8}
                        placeholder="-----BEGIN PRIVATE KEY-----"
                        required={slideOutMode === 'create'}
                      />
                    </div>

                    <div className="form-group">
                      <label className="form-label">Passphrase (Optional)</label>
                      <input
                        type="password"
                        value={credentialFields.passphrase}
                        onChange={(e) => setCredentialFields({...credentialFields, passphrase: e.target.value})}
                        className="form-input"
                        placeholder="Leave blank if key has no passphrase"
                      />
                    </div>
                  </>
                )}

                {/* Certificate Fields */}
                {formData.credential_type === 'certificate' && (
                  <>
                    <div className="form-group">
                      <label className="form-label">Certificate</label>
                      <div className="certificate-input-container">
                        <textarea
                          value={credentialFields.certificate}
                          onChange={(e) => setCredentialFields({...credentialFields, certificate: e.target.value})}
                          className="form-textarea"
                          rows={8}
                          placeholder="-----BEGIN CERTIFICATE-----&#10;Paste your certificate here...&#10;-----END CERTIFICATE-----"
                          required={slideOutMode === 'create'}
                        />
                        <div className="certificate-upload-section">
                          <div className="upload-divider">
                            <span>OR</span>
                          </div>
                          <input
                            type="file"
                            id="certificate-file"
                            accept=".crt,.cer,.pem,.p12,.pfx"
                            onChange={handleCertificateFileUpload}
                            className="file-input"
                            style={{ display: 'none' }}
                          />
                          <button
                            type="button"
                            onClick={() => document.getElementById('certificate-file')?.click()}
                            className="btn btn-outline"
                          >
                            Upload Certificate File
                          </button>
                          <small className="form-help">
                            Supported formats: .crt, .cer, .pem, .p12, .pfx
                          </small>
                        </div>
                      </div>
                    </div>

                    <div className="form-group">
                      <label className="form-label">Certificate Password (Optional)</label>
                      <input
                        type="password"
                        value={credentialFields.certificate_password}
                        onChange={(e) => setCredentialFields({...credentialFields, certificate_password: e.target.value})}
                        className="form-input"
                        placeholder="Required for password-protected certificates (e.g., .p12, .pfx)"
                      />
                    </div>
                  </>
                )}

                <div className="slide-out-actions">
                  <button type="button" onClick={closeSlideOut} className="btn btn-ghost">
                    Cancel
                  </button>
                  <button type="submit" className="btn btn-primary" disabled={saving}>
                    {saving ? 'Saving...' : slideOutMode === 'create' ? 'Create Credential' : 'Update Credential'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Credentials;