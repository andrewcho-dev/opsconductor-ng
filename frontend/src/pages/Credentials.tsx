import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Plus, Trash2, Check, X, Edit3, Upload, AlertTriangle, Clock } from 'lucide-react';
import { credentialApi } from '../services/api';
import { Credential, CredentialCreate, CredentialDecrypted } from '../types';

interface NewCredentialState {
  name: string;
  description: string;
  credential_type: 'password' | 'key' | 'certificate';
  username: string;
  password: string;
  domain: string;
  private_key: string;
  public_key: string;
  certificate: string;
  certificate_chain: string;
  passphrase: string;
  next_rotation_date: string;
}

const Credentials: React.FC = () => {
  const navigate = useNavigate();
  const { action, id } = useParams<{ action?: string; id?: string }>();
  const [credentials, setCredentials] = useState<CredentialDecrypted[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [addingNew, setAddingNew] = useState(false);
  const [editingCredential, setEditingCredential] = useState<CredentialDecrypted | null>(null);
  const [selectedCredential, setSelectedCredential] = useState<CredentialDecrypted | null>(null);
  
  // File upload refs
  const privateKeyUploadRef = useRef<HTMLInputElement>(null);
  const publicKeyUploadRef = useRef<HTMLInputElement>(null);
  const certificateUploadRef = useRef<HTMLInputElement>(null);
  const certificateChainUploadRef = useRef<HTMLInputElement>(null);

  const [newCredential, setNewCredential] = useState<NewCredentialState>({
    name: '',
    description: '',
    credential_type: 'password',
    username: '',
    password: '',
    domain: '',
    private_key: '',
    public_key: '',
    certificate: '',
    certificate_chain: '',
    passphrase: '',
    next_rotation_date: ''
  });

  useEffect(() => {
    if (action === 'add') {
      setAddingNew(true);
    }
    fetchCredentials();
  }, [action]);

  const fetchCredentials = async () => {
    try {
      setLoading(true);
      const response = await credentialApi.getAll();
      console.log('Fetched credentials:', response);
      setCredentials(response.credentials || []);
    } catch (error) {
      console.error('Failed to fetch credentials:', error);
      setCredentials([]);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = (field: keyof NewCredentialState, event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const content = e.target?.result as string;
        setNewCredential(prev => ({
          ...prev,
          [field]: content
        }));
      };
      reader.readAsText(file);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      
      // Validate required fields
      if (!newCredential.name.trim()) {
        alert('Credential name is required');
        return;
      }

      if (newCredential.description && newCredential.description.length > 20) {
        alert('Description must be 20 characters or less');
        return;
      }

      // For editing, allow partial updates (don't require password/key fields if not provided)
      const isEditing = !!editingCredential;
      
      // Validate based on credential type (only for new credentials)
      if (!isEditing) {
        if (newCredential.credential_type === 'password') {
          if (!newCredential.username || !newCredential.password) {
            alert('Username and password are required for password credentials');
            return;
          }
        } else if (newCredential.credential_type === 'key') {
          if (!newCredential.username || !newCredential.private_key) {
            alert('Username and private key are required for key credentials');
            return;
          }
        } else if (newCredential.credential_type === 'certificate') {
          if (!newCredential.certificate) {
            alert('Certificate is required for certificate credentials');
            return;
          }
        }
      }

      // Prepare credential data - only include non-empty fields for updates
      const credentialData: any = {
        name: newCredential.name,
        description: newCredential.description || undefined,
        credential_type: newCredential.credential_type,
        next_rotation_date: newCredential.next_rotation_date || undefined
      };

      // Only include fields that have values
      if (newCredential.username) credentialData.username = newCredential.username;
      if (newCredential.password) credentialData.password = newCredential.password;
      if (newCredential.domain) credentialData.domain = newCredential.domain;
      if (newCredential.private_key) credentialData.private_key = newCredential.private_key;
      if (newCredential.public_key) credentialData.public_key = newCredential.public_key;
      if (newCredential.certificate) credentialData.certificate = newCredential.certificate;
      if (newCredential.certificate_chain) credentialData.certificate_chain = newCredential.certificate_chain;
      if (newCredential.passphrase) credentialData.passphrase = newCredential.passphrase;

      if (isEditing) {
        await credentialApi.update(editingCredential.id, credentialData);
      } else {
        await credentialApi.create(credentialData);
      }
      
      await fetchCredentials();
      
      // Reset form and state
      handleCancelEdit();
      navigate('/credential-management');
    } catch (error: any) {
      console.error(`Failed to ${editingCredential ? 'update' : 'create'} credential:`, error);
      alert(error.response?.data?.detail || `Failed to ${editingCredential ? 'update' : 'create'} credential`);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (credentialId: number) => {
    if (!window.confirm('Are you sure you want to delete this credential?')) return;
    
    try {
      await credentialApi.delete(credentialId);
      await fetchCredentials();
    } catch (error) {
      console.error('Failed to delete credential:', error);
      alert('Failed to delete credential');
    }
  };

  const handleEdit = (credential: CredentialDecrypted) => {
    setEditingCredential(credential);
    setAddingNew(false);
    setSelectedCredential(null);
    
    // Populate the form with credential data
    setNewCredential({
      name: credential.name,
      description: credential.description || '',
      credential_type: credential.credential_type,
      username: credential.username || '',
      password: '', // Don't pre-fill passwords for security
      domain: credential.domain || '',
      private_key: '', // Don't pre-fill sensitive data
      public_key: '', 
      certificate: '',
      certificate_chain: '',
      passphrase: '',
      next_rotation_date: credential.next_rotation_date || ''
    });
  };

  const handleCancelEdit = () => {
    setEditingCredential(null);
    setAddingNew(false);
    setNewCredential({
      name: '',
      description: '',
      credential_type: 'password',
      username: '',
      password: '',
      domain: '',
      private_key: '',
      public_key: '',
      certificate: '',
      certificate_chain: '',
      passphrase: '',
      next_rotation_date: ''
    });
  };

  const isExpiringSoon = (validUntil: string | undefined) => {
    if (!validUntil) return false;
    const expiryDate = new Date(validUntil);
    const now = new Date();
    const thirtyDaysFromNow = new Date(now.getTime() + (30 * 24 * 60 * 60 * 1000));
    return expiryDate <= thirtyDaysFromNow;
  };

  const formatDate = (dateString: string | undefined) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString();
  };

  if (loading) {
    return <div className="loading">Loading credentials...</div>;
  }

  return (
    <div className="dense-dashboard">
      <style>{`
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
          margin-bottom: 8px;
          padding: 4px 0;
        }
        .header-left h1 {
          font-size: 18px;
          font-weight: 600;
          margin: 0;
          color: var(--neutral-800);
        }
        .header-actions {
          display: flex;
          gap: 6px;
        }
        
        .dashboard-grid {
          display: grid;
          grid-template-columns: 2fr 1fr;
          gap: 8px;
          height: calc(100vh - 120px);
        }
        
        .dashboard-section {
          background: white;
          border: 1px solid var(--neutral-200);
          border-radius: 6px;
          overflow: hidden;
          display: flex;
          flex-direction: column;
        }
        
        .section-header {
          padding: 8px 12px;
          background: var(--neutral-50);
          border-bottom: 1px solid var(--neutral-200);
          font-weight: 600;
          font-size: 12px;
          color: var(--neutral-700);
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        
        .compact-content {
          flex: 1;
          overflow: auto;
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
        
        .type-badge {
          display: inline-block;
          padding: 2px 8px;
          border-radius: 12px;
          font-size: 11px;
          font-weight: 500;
          text-transform: uppercase;
        }
        
        .type-password {
          background: var(--blue-100);
          color: var(--blue-700);
        }
        
        .type-key {
          background: var(--green-100);
          color: var(--green-700);
        }
        
        .type-certificate {
          background: var(--purple-100);
          color: var(--purple-700);
        }
        
        .expiry-warning {
          display: flex;
          align-items: center;
          gap: 4px;
          color: var(--orange-600);
        }
        
        .expiry-critical {
          color: var(--red-600);
        }
        
        .actions {
          display: flex;
          gap: 4px;
        }
        
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
        
        .radio-group {
          display: flex;
          gap: 16px;
          margin-top: 4px;
        }
        
        .radio-option {
          display: flex;
          align-items: center;
          gap: 6px;
          cursor: pointer;
          font-size: 12px;
          font-weight: 500;
        }
        
        .radio-option input[type="radio"] {
          margin: 0;
          cursor: pointer;
        }
        
        .credential-type-section {
          padding: 16px;
          background: var(--neutral-25);
          border-bottom: 1px solid var(--neutral-200);
          margin-bottom: 0;
        }
        
        .credential-type-section .form-label {
          margin-bottom: 8px;
          display: block;
        }
        
        .form-grid {
          display: grid;
          grid-template-columns: 1fr 2fr;
          gap: 24px;
          align-items: start;
        }
        
        .form-grid-left {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
        
        .form-grid-right {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
        
        .key-field {
          position: relative;
        }
        
        .key-field .form-textarea {
          padding-right: 40px;
        }
        
        .upload-icon {
          position: absolute;
          top: 8px;
          right: 8px;
          background: none;
          border: none;
          color: var(--neutral-500);
          cursor: pointer;
          padding: 4px;
          border-radius: 4px;
          transition: color 0.2s ease;
        }
        
        .upload-icon:hover {
          color: var(--neutral-700);
          background: var(--neutral-100);
        }
        
        .table-container {
          overflow: auto;
        }
        
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
        
        .form-header {
          padding: 16px 20px;
          border-bottom: 1px solid var(--neutral-200);
          background: var(--neutral-50);
        }
        
        .form-title {
          font-size: 16px;
          font-weight: 600;
          color: var(--neutral-900);
        }
        
        .form-content {
          padding: 20px;
        }
        
        .form-field {
          margin-bottom: 16px;
        }
        
        .form-label {
          display: block;
          font-size: 12px;
          font-weight: 600;
          color: var(--neutral-700);
          margin-bottom: 4px;
        }
        
        .form-label.required::after {
          content: ' *';
          color: var(--red-600);
        }
        
        .form-input {
          width: 100%;
          padding: 8px 12px;
          border: 1px solid var(--neutral-300);
          border-radius: 4px;
          font-size: 14px;
          color: var(--neutral-900);
        }
        
        .form-input:focus {
          outline: none;
          border-color: var(--primary-blue);
          box-shadow: 0 0 0 2px var(--blue-100);
        }
        
        .form-textarea {
          resize: vertical;
          min-height: 100px;
          font-family: 'Courier New', monospace;
          font-size: 12px;
        }
        
        .form-select {
          width: 100%;
          padding: 8px 12px;
          border: 1px solid var(--neutral-300);
          border-radius: 4px;
          font-size: 14px;
          background: white;
          cursor: pointer;
        }
        
        .upload-container {
          display: flex;
          gap: 8px;
          align-items: end;
        }
        
        .upload-container .form-input {
          flex: 1;
        }
        
        .btn-upload {
          display: flex;
          align-items: center;
          gap: 4px;
          padding: 8px 12px;
          background: var(--neutral-100);
          border: 1px solid var(--neutral-300);
          border-radius: 4px;
          font-size: 12px;
          cursor: pointer;
          white-space: nowrap;
        }
        
        .btn-upload:hover {
          background: var(--neutral-200);
        }
        
        .hidden {
          display: none;
        }
        
        .form-actions {
          display: flex;
          gap: 8px;
          padding: 16px 20px;
          border-top: 1px solid var(--neutral-200);
          background: var(--neutral-50);
        }
        
        .btn-secondary {
          background: var(--neutral-100);
          color: var(--neutral-700);
          border: 1px solid var(--neutral-300);
        }
        
        .btn-secondary:hover {
          background: var(--neutral-200);
        }
        
        .empty-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 48px 24px;
          text-align: center;
          color: var(--neutral-500);
        }
        
        .char-count {
          font-size: 11px;
          color: var(--neutral-500);
          text-align: right;
          margin-top: 2px;
        }
        
        .char-count.error {
          color: var(--red-600);
        }
      `}</style>

      {/* Dashboard-style header */}
      <div className="dashboard-header">
        <div className="header-left">
          <h1>Credential Management</h1>
        </div>
        <div className="header-actions">
          <button 
            className="btn-icon btn-success"
            onClick={() => {
              setAddingNew(true);
              setEditingCredential(null);
              setSelectedCredential(null);
            }}
            title="Add Credential"
            disabled={addingNew || !!editingCredential}
          >
            <Plus size={16} />
          </button>
        </div>
      </div>

      {/* 2-column dashboard grid */}
      <div className="dashboard-grid">
        {/* Column 1: Credentials Table */}
        <div className="dashboard-section">
          <div className="section-header">
            Credentials ({credentials.length})
          </div>
          <div className="compact-content">
          
          {credentials.length === 0 ? (
            <div className="empty-state">
              <h3>No credentials found</h3>
              <p>Create your first credential to start managing authentication.</p>
              <button 
                className="btn-icon btn-success"
                onClick={() => {
                  setAddingNew(true);
                  setEditingCredential(null);
                  setSelectedCredential(null);
                }}
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
                  <th>Validity</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {credentials.map((credential) => (
                  <tr 
                    key={credential.id} 
                    className={selectedCredential?.id === credential.id ? 'selected' : ''}
                    onClick={() => setSelectedCredential(credential)}
                  >
                    <td>
                      <div style={{ fontWeight: '500' }}>{credential.name}</div>
                      {credential.description && (
                        <div style={{ fontSize: '12px', color: 'var(--neutral-600)' }}>
                          {credential.description}
                        </div>
                      )}
                    </td>
                    <td>
                      <span className={`type-badge type-${credential.credential_type}`}>
                        {credential.credential_type}
                      </span>
                    </td>
                    <td>{credential.username || '-'}</td>
                    <td>
                      {credential.valid_until ? (
                        <div className={isExpiringSoon(credential.valid_until) ? 'expiry-warning' : ''}>
                          {isExpiringSoon(credential.valid_until) && (
                            <AlertTriangle size={14} />
                          )}
                          {formatDate(credential.valid_until)}
                        </div>
                      ) : (
                        credential.next_rotation_date ? (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                            <Clock size={14} />
                            {formatDate(credential.next_rotation_date)}
                          </div>
                        ) : '-'
                      )}
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '4px' }}>
                        <button 
                          className="btn-icon btn-ghost"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleEdit(credential);
                          }}
                          title="Edit credential"
                        >
                          <Edit3 size={16} />
                        </button>
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

        {/* Column 2: Credential Details/Form */}
        <div className="dashboard-section">
          {addingNew || editingCredential ? (
            <>
              <div className="section-header">
                <span>{editingCredential ? `Edit Credential: ${editingCredential.name}` : 'Create New Credential'}</span>
                <div style={{ display: 'flex', gap: '4px' }}>
                  <button 
                    className="btn-icon btn-success"
                    onClick={handleSave}
                    disabled={saving}
                    title={editingCredential ? "Update Credential" : "Create Credential"}
                  >
                    <Check size={16} />
                  </button>
                  <button 
                    className="btn-icon btn-ghost"
                    onClick={handleCancelEdit}
                    disabled={saving}
                    title="Cancel"
                  >
                    <X size={16} />
                  </button>
                </div>
              </div>
              {/* Credential Type Selection - Own Section */}
              <div className="credential-type-section">
                <label className="form-label required">Credential Type</label>
                <div className="radio-group">
                  <label className="radio-option">
                    <input
                      type="radio"
                      name="credential_type"
                      value="password"
                      checked={newCredential.credential_type === 'password'}
                      onChange={(e) => setNewCredential(prev => ({ 
                        ...prev, 
                        credential_type: e.target.value as 'password' | 'key' | 'certificate' 
                      }))}
                    />
                    <span>Password</span>
                  </label>
                  <label className="radio-option">
                    <input
                      type="radio"
                      name="credential_type"
                      value="key"
                      checked={newCredential.credential_type === 'key'}
                      onChange={(e) => setNewCredential(prev => ({ 
                        ...prev, 
                        credential_type: e.target.value as 'password' | 'key' | 'certificate' 
                      }))}
                    />
                    <span>SSH Key</span>
                  </label>
                  <label className="radio-option">
                    <input
                      type="radio"
                      name="credential_type"
                      value="certificate"
                      checked={newCredential.credential_type === 'certificate'}
                      onChange={(e) => setNewCredential(prev => ({ 
                        ...prev, 
                        credential_type: e.target.value as 'password' | 'key' | 'certificate' 
                      }))}
                    />
                    <span>Certificate</span>
                  </label>
                </div>
              </div>

              {/* Form Fields Section */}
              <div className="compact-content credential-details">

              {/* Password form - single column layout */}
              {newCredential.credential_type === 'password' && (
                <>
                  <div className="form-field">
                    <label className="form-label required">Name</label>
                    <input
                      type="text"
                      className="form-input"
                      value={newCredential.name}
                      onChange={(e) => setNewCredential(prev => ({ ...prev, name: e.target.value }))}
                    />
                  </div>

                  <div className="form-field">
                    <label className="form-label">Description</label>
                    <input
                      type="text"
                      className="form-input"
                      value={newCredential.description}
                      onChange={(e) => {
                        const value = e.target.value;
                        if (value.length <= 20) {
                          setNewCredential(prev => ({ ...prev, description: value }));
                        }
                      }}
                      maxLength={20}
                    />
                  </div>

                  <div className="form-field">
                    <label className="form-label required">Username</label>
                    <input
                      type="text"
                      className="form-input"
                      value={newCredential.username}
                      onChange={(e) => setNewCredential(prev => ({ ...prev, username: e.target.value }))}
                    />
                  </div>

                  <div className="form-field">
                    <label className="form-label required">Password</label>
                    <input
                      type="password"
                      className="form-input"
                      value={newCredential.password}
                      onChange={(e) => setNewCredential(prev => ({ ...prev, password: e.target.value }))}
                    />
                  </div>

                  <div className="form-field">
                    <label className="form-label">Domain</label>
                    <input
                      type="text"
                      className="form-input"
                      value={newCredential.domain}
                      onChange={(e) => setNewCredential(prev => ({ ...prev, domain: e.target.value }))}
                    />
                  </div>

                  <div className="form-field">
                    <label className="form-label">Next Rotation Date</label>
                    <input
                      type="date"
                      className="form-input"
                      value={newCredential.next_rotation_date}
                      onChange={(e) => setNewCredential(prev => ({ ...prev, next_rotation_date: e.target.value }))}
                    />
                  </div>
                </>
              )}

              {/* SSH Key form - grid layout */}
              {newCredential.credential_type === 'key' && (
                <div className="form-grid">
                  <div className="form-grid-left">
                    <div className="form-field">
                      <label className="form-label required">Name</label>
                      <input
                        type="text"
                        className="form-input"
                        value={newCredential.name}
                        onChange={(e) => setNewCredential(prev => ({ ...prev, name: e.target.value }))}
                      />
                    </div>

                    <div className="form-field">
                      <label className="form-label required">Username</label>
                      <input
                        type="text"
                        className="form-input"
                        value={newCredential.username}
                        onChange={(e) => setNewCredential(prev => ({ ...prev, username: e.target.value }))}
                      />
                    </div>

                    <div className="form-field">
                      <label className="form-label">Description</label>
                      <input
                        type="text"
                        className="form-input"
                        value={newCredential.description}
                        onChange={(e) => {
                          const value = e.target.value;
                          if (value.length <= 20) {
                            setNewCredential(prev => ({ ...prev, description: value }));
                          }
                        }}
                        maxLength={20}
                      />
                    </div>

                    <div className="form-field">
                      <label className="form-label">Next Rotation Date</label>
                      <input
                        type="date"
                        className="form-input"
                        value={newCredential.next_rotation_date}
                        onChange={(e) => setNewCredential(prev => ({ ...prev, next_rotation_date: e.target.value }))}
                      />
                    </div>
                  </div>

                  <div className="form-grid-right">
                    <div className="form-field key-field">
                      <label className="form-label required">Private Key</label>
                      <textarea
                        className="form-input form-textarea"
                        value={newCredential.private_key}
                        onChange={(e) => setNewCredential(prev => ({ ...prev, private_key: e.target.value }))}
                        rows={8}
                      />
                      <button
                        type="button"
                        className="upload-icon"
                        onClick={() => privateKeyUploadRef.current?.click()}
                        title="Upload file"
                      >
                        <Upload size={16} />
                      </button>
                      <input
                        ref={privateKeyUploadRef}
                        type="file"
                        className="hidden"
                        accept=".pem,.key,.ppk"
                        onChange={(e) => handleFileUpload('private_key', e)}
                      />
                    </div>

                    <div className="form-field key-field">
                      <label className="form-label">Public Key</label>
                      <textarea
                        className="form-input form-textarea"
                        value={newCredential.public_key}
                        onChange={(e) => setNewCredential(prev => ({ ...prev, public_key: e.target.value }))}
                        rows={4}
                      />
                      <button
                        type="button"
                        className="upload-icon"
                        onClick={() => publicKeyUploadRef.current?.click()}
                        title="Upload file"
                      >
                        <Upload size={16} />
                      </button>
                      <input
                        ref={publicKeyUploadRef}
                        type="file"
                        className="hidden"
                        accept=".pub,.pem"
                        onChange={(e) => handleFileUpload('public_key', e)}
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Certificate form - grid layout */}
              {newCredential.credential_type === 'certificate' && (
                <div className="form-grid">
                  <div className="form-grid-left">
                    <div className="form-field">
                      <label className="form-label required">Name</label>
                      <input
                        type="text"
                        className="form-input"
                        value={newCredential.name}
                        onChange={(e) => setNewCredential(prev => ({ ...prev, name: e.target.value }))}
                      />
                    </div>

                    <div className="form-field">
                      <label className="form-label">Description</label>
                      <input
                        type="text"
                        className="form-input"
                        value={newCredential.description}
                        onChange={(e) => {
                          const value = e.target.value;
                          if (value.length <= 20) {
                            setNewCredential(prev => ({ ...prev, description: value }));
                          }
                        }}
                        maxLength={20}
                      />
                    </div>
                  </div>

                  <div className="form-grid-right">
                    <div className="form-field key-field">
                      <label className="form-label required">Private Key</label>
                      <textarea
                        className="form-input form-textarea"
                        value={newCredential.private_key}
                        onChange={(e) => setNewCredential(prev => ({ ...prev, private_key: e.target.value }))}
                        rows={6}
                      />
                      <button
                        type="button"
                        className="upload-icon"
                        onClick={() => privateKeyUploadRef.current?.click()}
                        title="Upload file"
                      >
                        <Upload size={16} />
                      </button>
                      <input
                        ref={privateKeyUploadRef}
                        type="file"
                        className="hidden"
                        accept=".pem,.key,.ppk"
                        onChange={(e) => handleFileUpload('private_key', e)}
                      />
                    </div>

                    <div className="form-field key-field">
                      <label className="form-label required">Certificate</label>
                      <textarea
                        className="form-input form-textarea"
                        value={newCredential.certificate}
                        onChange={(e) => setNewCredential(prev => ({ ...prev, certificate: e.target.value }))}
                        rows={6}
                      />
                      <button
                        type="button"
                        className="upload-icon"
                        onClick={() => certificateUploadRef.current?.click()}
                        title="Upload file"
                      >
                        <Upload size={16} />
                      </button>
                      <input
                        ref={certificateUploadRef}
                        type="file"
                        className="hidden"
                        accept=".crt,.cer,.pem"
                        onChange={(e) => handleFileUpload('certificate', e)}
                      />
                    </div>

                    <div className="form-field key-field">
                      <label className="form-label">Certificate Chain</label>
                      <textarea
                        className="form-input form-textarea"
                        value={newCredential.certificate_chain}
                        onChange={(e) => setNewCredential(prev => ({ ...prev, certificate_chain: e.target.value }))}
                        rows={4}
                      />
                      <button
                        type="button"
                        className="upload-icon"
                        onClick={() => certificateChainUploadRef.current?.click()}
                        title="Upload file"
                      >
                        <Upload size={16} />
                      </button>
                      <input
                        ref={certificateChainUploadRef}
                        type="file"
                        className="hidden"
                        accept=".pem,.crt"
                        onChange={(e) => handleFileUpload('certificate_chain', e)}
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Passphrase field - shown for key and certificate types when they have content */}
              {(newCredential.credential_type === 'key' || newCredential.credential_type === 'certificate') && 
               (newCredential.private_key || newCredential.certificate) && (
                <div className="form-field">
                  <label className="form-label">Passphrase</label>
                  <input
                    type="password"
                    className="form-input"
                    value={newCredential.passphrase}
                    onChange={(e) => setNewCredential(prev => ({ ...prev, passphrase: e.target.value }))}
                  />
                </div>
              )}
            </div>


            </>
          ) : selectedCredential ? (
            <>
              <div className="section-header">
                Credential Details
              </div>
              <div className="compact-content credential-details">
                <h3>{selectedCredential.name}</h3>
                
                <div className="detail-group">
                  <div className="detail-label">Type</div>
                  <div className="detail-value">
                    <span className={`type-badge type-${selectedCredential.credential_type}`}>
                      {selectedCredential.credential_type}
                    </span>
                  </div>
                </div>

                {selectedCredential.description && (
                  <div className="detail-group">
                    <div className="detail-label">Description</div>
                    <div className="detail-value">{selectedCredential.description}</div>
                  </div>
                )}

                {selectedCredential.username && (
                  <div className="detail-group">
                    <div className="detail-label">Username</div>
                    <div className="detail-value">{selectedCredential.username}</div>
                  </div>
                )}

                {selectedCredential.domain && (
                  <div className="detail-group">
                    <div className="detail-label">Domain</div>
                    <div className="detail-value">{selectedCredential.domain}</div>
                  </div>
                )}

                {selectedCredential.valid_until && (
                  <div className="detail-group">
                    <div className="detail-label">Valid Until</div>
                    <div className={`detail-value ${isExpiringSoon(selectedCredential.valid_until) ? 'expiry-warning' : ''}`}>
                      {isExpiringSoon(selectedCredential.valid_until) && <AlertTriangle size={14} />}
                      {formatDate(selectedCredential.valid_until)}
                    </div>
                  </div>
                )}

                {selectedCredential.next_rotation_date && (
                  <div className="detail-group">
                    <div className="detail-label">Next Rotation</div>
                    <div className="detail-value">
                      <Clock size={14} style={{ marginRight: '4px' }} />
                      {formatDate(selectedCredential.next_rotation_date)}
                    </div>
                  </div>
                )}

                <div className="detail-group">
                  <div className="detail-label">Created</div>
                  <div className="detail-value">{formatDate(selectedCredential.created_at)}</div>
                </div>
              </div>
            </>
          ) : (
            <>
              <div className="section-header">
                Select Credential
              </div>
              <div className="compact-content">
                <div className="empty-state">
                  <h3>Select a credential</h3>
                  <p>Select a credential from the table to view details and manage authentication settings.</p>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default Credentials;